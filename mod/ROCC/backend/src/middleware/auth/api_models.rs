use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, utoipa::ToSchema)]
pub struct LoginRequest {
    pub username: String,
    pub password: String,
} // Note: username and password are not required fields

#[derive(Debug, Serialize, Deserialize, utoipa::ToSchema)]
pub struct SignUpRequest{
    pub name: String, 
    pub surname: String, 
    pub age: i32, 
    pub username: String, 
    pub email: String, 
    pub password: String, 
    pub role: String, 
    pub avatar: String,
}




#[derive(Serialize)]
pub struct ErrorResponse {
    pub error: String,
}