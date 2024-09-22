use std::io::Error;
use actix_service::{Service, Transform};
use actix_web::{body::{BoxBody, MessageBody}, dev::{ServiceRequest, ServiceResponse}, HttpResponse};
use bcrypt::{hash, verify, DEFAULT_COST};
use rand::{thread_rng, Rng};
use jsonwebtoken::{encode, Header, EncodingKey};
use chrono::Utc;
use futures::future::{ok, LocalBoxFuture, Ready};
use futures::FutureExt;
use std::task::{Context, Poll};
use super::claims::Claims;
pub struct PasswordManager;

impl PasswordManager{
    pub fn generate_password(length: u8, use_special_chars: bool, use_numbers: bool) -> Result<String, Error> {
        let mut rng = thread_rng();
        let mut password = String::with_capacity(length as usize);
        let mut charset = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ".to_vec();

        if use_special_chars {
            charset.extend(b"!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~");
        }

        if use_numbers {
            charset.extend(b"0123456789");
        }

        for _ in 0..length {
            let idx = rng.gen_range(0..charset.len());
            password.push(charset[idx] as char);
        }

        Ok(password)
    }
    pub fn hash_password(pwd: &str) -> Result<String, bcrypt::BcryptError>{
        hash(pwd, DEFAULT_COST)
    }
    pub fn verify_password(pwd: &str, hashed_pwd: &str) -> Result<bool, bcrypt::BcryptError>{
        verify(pwd, hashed_pwd)
    }
}

pub async fn generate_token(user_id: i32) -> Result<String, String> {
    let claims = Claims {
        sub: user_id,
        exp: (Utc::now() + chrono::Duration::hours(24)).timestamp() as usize,
    };

    match encode(
        &Header::default(),
        &claims,
        &EncodingKey::from_secret(b"10"),
    ) {
        Ok(token) => Ok(token),
        Err(e) => Err(format!("Failed to generate token: {}", e)),
    }
}

use jsonwebtoken::{decode, DecodingKey, Validation};

pub async fn verify_token(token: &str) -> Result<Claims, String> {
    let decoding_key = DecodingKey::from_secret(b"10");
    let validation = Validation::default();

    match decode::<Claims>(token, &decoding_key, &validation) {
        Ok(decoded) => Ok(decoded.claims),
        Err(e) => Err(format!("Token verification failed: {}", e)),
    }
}

