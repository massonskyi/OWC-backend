use crate::middleware::auth;

use utoipa::OpenApi;
use actix_web::HttpResponse;



#[derive(OpenApi)]
#[openapi(
    paths(
        auth::api::sign_in,
        auth::api::sign_up
    ),
    components(
        schemas(
            auth::api_models::SignUpRequest,
            auth::api_models::LoginRequest
        )
    )
)]
struct ApiDoc;

pub async fn get_openapi() -> HttpResponse {
    HttpResponse::Ok().json(ApiDoc::openapi())
}
