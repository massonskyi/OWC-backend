use actix_web::{web, HttpResponse, Responder};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use crate::middleware::auth::manager::UserManager;
use super::models::UserProfile;






pub fn init(cfg: &mut web::ServiceConfig) {
    cfg.service(
        web::resource("/profile")
            .route(web::get().to(get_profile))
            .route(web::put().to(update_profile))
            .route(web::delete().to(delete_profile))
    );
}


#[utoipa::path(
    get,
    path = "/profile",
    responses(
        (status = 200, description = "Returns user profile", body = UserProfile),
        (status = 404, description = "Profile not found")
    )
)]
async fn get_profile(data: web::Data<Arc<RwLock<UserManager>>>, user_id: web::Path<i32>) -> impl Responder {
    let manager = data.read().await;
    match manager.get_profile(user_id.into_inner()).await {
        Some(profile) => HttpResponse::Ok().json(profile),
        None => HttpResponse::NotFound().body("Profile not found"),
    }
}

#[utoipa::path(
    put,
    path = "/profile",
    request_body = UserProfile,
    responses(
        (status = 200, description = "Profile updated", body = UserProfile),
        (status = 400, description = "Bad Request"),
        (status = 404, description = "Profile not found")
    )
)]
async fn update_profile(data: web::Data<Arc<RwLock<UserManager>>>, user_id: web::Path<i32>, profile_data: web::Json<UserProfile>) -> impl Responder {
    let mut update_data = HashMap::new();
    update_data.insert("name".to_string(), profile_data.name.clone());
    update_data.insert("surname".to_string(), profile_data.surname.clone());
    update_data.insert("email".to_string(), profile_data.email.clone());
    update_data.insert("username".to_string(), profile_data.username.clone());

    let manager = data.write().await;
    match manager.update_profile(user_id.into_inner(), update_data).await {
        Ok(profile) => HttpResponse::Ok().json(profile),
        Err(e) => HttpResponse::InternalServerError().body(e),
    }
}

#[utoipa::path(
    delete,
    path = "/profile",
    responses(
        (status = 200, description = "Profile deleted"),
        (status = 404, description = "Profile not found")
    )
)]
async fn delete_profile(data: web::Data<Arc<RwLock<UserManager>>>, user_id: web::Path<i32>) -> impl Responder {
    let manager = data.write().await;
    match manager.delete_profile(user_id.into_inner()).await {
        Ok(_) => HttpResponse::Ok().body("Profile deleted"),
        Err(e) => HttpResponse::InternalServerError().body(e),
    }
}