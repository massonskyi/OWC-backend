use actix_cors::Cors;
use actix_files::Files;
use actix_service::Service;
use actix_web::{middleware::Logger, web, App, HttpResponse, HttpServer, Responder};
use actix_web_httpauth::middleware::HttpAuthentication;
use std::sync::Arc;

mod middleware;
mod core;
mod logger;
mod tools;
mod functions;
use tools::create_logger_file;
use logger::logger::AsyncLogger;
use core::database::db_core;


use middleware::
{
    api::utopia_swagger, auth::
    {
        auth_middleware::auth_middleware, claims::validate, handlers, manager::UserManager
    }, profile
};

// Измените render_start_page на статический текст
async fn render_start_page() -> &'static str {
    r#"
    <html>
        <body>
            <h1>Hello on start page!</h1>
            <p>Go to the following pages:</p>
            <ul>
                <li><a href="/users">Users</a></li>
                <li><a href="/api-doc/openapi.json">API</a></li>
            </ul>
        </body>
    </html>
    "#
}

async fn index() -> impl Responder {
    HttpResponse::Ok().body(render_start_page())
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    let file_path = match create_logger_file() {
        Ok(path) => path,
        Err(e) => {
            eprintln!("Error creating log file path: {}", e);
            return Err(std::io::Error::new(std::io::ErrorKind::Other, e.to_string()));
        }
    };

    let logger = AsyncLogger::new(&file_path);
    match logger.init().await {
        Ok(_) => {},
        Err(e) => {
            eprintln!("Error initializing logger: {}", e);
            return Err(std::io::Error::new(std::io::ErrorKind::Other, e.to_string()));
        }
    };

    let host = std::env::var("HOST").unwrap_or_else(|_| "0.0.0.0".to_string());
    let port = 8050;

    let db_url = match db_core::establish_connection() {
        Ok(path) => path,
        Err(e) => {
            eprintln!("Error creating db connection: {}", e);
            return Err(std::io::Error::new(std::io::ErrorKind::Other, e.to_string()));
        }
    };

    let bearer_middleware = HttpAuthentication::bearer(validate);
    let user_manager = Arc::new(tokio::sync::RwLock::new(
        UserManager::new(&db_url).await.expect("Failed to create UserManager")
    ));

    logger.b_info(&format!("Server started at http://{}:{}/", host, port)).await;

    HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(user_manager.clone()))
            .wrap(
                Cors::default()
                    .allow_any_origin()
                    .allow_any_method()
                    .allow_any_header()
                    .max_age(3600)
                    .supports_credentials() // Поддержка отправки куки
            )
            .wrap_fn(|req, srv| {
                let fut = srv.call(req);
                let next = move |req| {
                    let fut = fut.clone();
                    Box::pin(async move {
                        fut.await
                    })
                };
                Box::pin(async move {
                    let result = auth_middleware(req, next).await;
                    result
                })
            })
            .configure(handlers::init)
            .configure(profile::handlers::init)
            .route("/", web::get().to(index))
            .route("/api-doc/openapi.json", web::get().to(utopia_swagger::get_openapi))
    })
    .bind(format!("{}:{}", host, port))?
    .run()
    .await
}