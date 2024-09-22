use actix_service::{Service, Transform};
use actix_web::{dev::ServiceRequest, dev::ServiceResponse, Error, HttpMessage, HttpResponse};
use actix_web::body::BoxBody;
use bytes::Bytes;
use futures::future::{ok, Ready};
use futures::Future;
use std::pin::Pin;
use std::rc::Rc;
use std::task::{Context, Poll};

use super::utils::verify_token;

pub struct AuthMiddleware<S, B> {
    service: Rc<S>,
    _marker: std::marker::PhantomData<B>,
}

impl<S, B> Service<ServiceRequest> for AuthMiddleware<S, B>
where
    S: Service<ServiceRequest, Response = ServiceResponse<B>, Error = Error> + 'static,
    B: 'static + actix_web::body::MessageBody + From<Bytes> + Default,
{
    type Response = ServiceResponse<B>;
    type Error = Error;
    type Future = Pin<Box<dyn Future<Output = Result<Self::Response, Self::Error>>>>;

    fn poll_ready(&self, cx: &mut Context<'_>) -> Poll<Result<(), Self::Error>> {
        self.service.poll_ready(cx)
    }

    fn call(&self, req: ServiceRequest) -> Self::Future {
        let auth_header = req.headers().get("Authorization");

        if let Some(header) = auth_header {
            if let Ok(token) = header.to_str() {
                let service = Rc::clone(&self.service);
                return Box::pin(async move {
                    if let Ok(_claims) = verify_token(token).await {
                        let res = service.call(req).await?;
                        Ok(res)
                    } else {
                        let res = HttpResponse::Unauthorized().finish().map_into_boxed_body();
                        let service_response = ServiceResponse::new(req.request().clone(), res);
                        Ok(service_response.map_into_left_body())
                    }
                });
            }
        }

        let res = HttpResponse::Unauthorized().finish().map_into_boxed_body();
        let service_response = ServiceResponse::new(req.request().clone(), res);
        Box::pin(async move { Ok(service_response.map_into_left_body()) })
    }
}