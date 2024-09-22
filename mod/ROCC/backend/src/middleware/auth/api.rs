use actix_web::{cookie::{Cookie, SameSite}, web, HttpResponse, Responder};
use bcrypt::{hash, verify, DEFAULT_COST};
use chrono::Utc;
use jsonwebtoken::{encode, Header, EncodingKey};
use std::sync::Arc;
use tokio::sync::RwLock;

use super::{claims::Claims, manager::UserManager, api_models::{LoginRequest, SignUpRequest, ErrorResponse}};  // Assuming UserManager is implemented elsewhere

#[utoipa::path(
    post,  // POST method allows request body
    request_body = LoginRequest,
    path = "/sign_in",
    responses(
        (status = 200, description = "Successful response with JWT token set as a cookie and returned in the response body", body = String), // Returning token as string
        (status = 401, description = "Unauthorized response", body = String),
        (status = 403, description = "Forbidden response", body = String),
        (status = 500, description = "Internal server error", body = String),
    )
)]
pub async fn sign_in(
    user_manager: web::Data<Arc<RwLock<UserManager>>>, 
    req: web::Json<LoginRequest>
) -> impl Responder {
    // Obtain mutable access to UserManager
    let manager = user_manager.read().await;

    // Retrieve user by username
    let user = match manager.get_user_by_username(&req.username).await {
        Ok(Some(user)) => user,
        Ok(None) => {
            eprintln!("User not found");
            return HttpResponse::Unauthorized().finish(); // User not found
        },
        Err(e) => {
            eprintln!("Error retrieving user: {:?}", e);
            return HttpResponse::InternalServerError().finish();
        },
    };

    // Verify password using bcrypt
    let password_match = match verify(&req.password, &user.hash_password) {
        Ok(matched) => matched,
        Err(e) => {
            eprintln!("Error verifying password: {:?}", e);
            return HttpResponse::Unauthorized().finish(); // Error verifying password
        },
    };

    if !password_match {
        eprintln!("Password does not match for user: {}", user.username);
        return HttpResponse::Unauthorized().finish(); // Incorrect password
    }

    // Generate JWT token for the authenticated user
    let claims = Claims {
        sub: user.id,
        exp: (Utc::now() + chrono::Duration::hours(24)).timestamp() as usize, // Token expires in 24 hours
    };

    let token = match encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(b"secret"), // Replace with your actual secret key
    ) {
        Ok(t) => t,
        Err(e) => {
            eprintln!("Error encoding token: {:?}", e);
            return HttpResponse::InternalServerError().finish();
        },
    };
;

    // Проверка и установка куки
    let cookie = Cookie::build("auth_token", token.clone())
        .path("/") // Доступен на всем сайте
        .http_only(true) // Доступен только для HTTP
        .secure(false) // Используйте true для HTTPS
        .same_site(SameSite::Lax) // Разрешить кросс-сайтовые запросы
        .finish();

    let response = HttpResponse::Ok()
        .cookie(cookie) // Добавление куки в ответ
        .json("Successfully login"); // Отправка ответа

    println!("Response Headers: {:?}", response.headers());
    
    response
}

#[utoipa::path(
    post,
    path = "/sign_up",
    request_body = SignUpRequest,
    responses(
        (status = 200, description = "Successful response with JWT token set as a cookie and returned in the response body", body = String), // JWT token as a string
        (status = 401, description = "Unauthorized response", body = String),
        (status = 403, description = "Forbidden response", body = String),
        (status = 500, description = "Internal server error", body = String)
    )
)]
pub async fn sign_up(
    user_manager: web::Data<Arc<RwLock<UserManager>>>,
    req: web::Json<SignUpRequest>
) -> impl Responder {
    // Clone necessary fields from SignUpRequest
    let username = req.username.clone();
    let email = req.email.clone();
    let role = req.role.clone();
    let avatar = req.avatar.clone();

    // Obtain mutable access to UserManager
    let manager = user_manager.write().await;

    // Create the user in the database
    let user = match manager.create_user(
        req.name.clone(),
        req.surname.clone(),
        req.age,
        username.clone(),
        email,
        req.password.clone(),
        role,
        avatar,
    ).await {
        Ok(user) => user,
        Err(e) => {
            eprintln!("User creation failed: {}", e);
            return HttpResponse::InternalServerError().json(ErrorResponse {
                error: "Failed to create user".to_string(),
            });
        },
    };

    // Generate JWT token for the newly created user
    let claims = Claims {
        sub: user.id,
        exp: (Utc::now() + chrono::Duration::hours(24)).timestamp() as usize, // Token expires in 24 hours
    };

    let token = match encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(b"test"), // Replace with your actual secret key
    ) {
        Ok(t) => t,
        Err(e) => {
            eprintln!("JWT token encoding failed: {}", e);
            return HttpResponse::InternalServerError().json(ErrorResponse {
                error: "Failed to generate token".to_string(),
            });
        },
    };

    let cookie = Cookie::build("auth_token", token.clone())
        .path("/") // Доступен на всем сайте
        .http_only(true) // Доступен только для HTTP
        .secure(false) // Используйте true для HTTPS
        .same_site(SameSite::Lax) // Разрешить кросс-сайтовые запросы
        .finish();

    let response = HttpResponse::Ok()
        .cookie(cookie) // Добавление куки в ответ
        .json("Successfully registered"); // Отправка ответа

    println!("Response Headers: {:?}", response.headers());

    response

}