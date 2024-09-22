use actix_web::{web, HttpResponse, Responder};

pub async fn create_workspace_handler(
    user: UserModel,
    form: web::Json<WorkspaceModel>,
) -> impl Responder {
    let new_workspace = WorkspaceManager::create_workspace(
        form.name.clone(),
        form.description.clone(),
        user.id,
        form.docker_container.image.clone(),
    );
    
    HttpResponse::Ok().json(new_workspace)
}

pub async fn update_workspace_handler(
    user: UserModel,
    form: web::Json<WorkspaceModel>,
    workspace_id: web::Path<i32>,
) -> impl Responder {
    // Здесь вы должны загрузить воркспейс из базы данных, например, используя workspace_id
    let mut workspace = WorkspaceModel {
        id: *workspace_id,
        name: form.name.clone(),
        description: form.description.clone(),
        owner_id: user.id,
        created_at: "".to_string(),
        updated_at: "".to_string(),
        deleted_at: None,
    };
    
    WorkspaceManager::update_workspace(&mut workspace, form.name.clone(), form.description.clone());
    
    HttpResponse::Ok().json(workspace)
}

pub async fn delete_workspace_handler(
    user: UserModel,
    workspace_id: web::Path<i32>,
) -> impl Responder {
    // Здесь вы должны загрузить воркспейс из базы данных, например, используя workspace_id
    let mut workspace = WorkspaceModel {
        id: *workspace_id,
        name: "dummy".to_string(),
        description: None,
        owner_id: user.id,
        created_at: "".to_string(),
        updated_at: "".to_string(),
        deleted_at: None,
    };
    
    WorkspaceManager::delete_workspace(&mut workspace);
    
    HttpResponse::Ok().json(workspace)
}

pub async fn get_workspaces_handler(user: UserModel) -> impl Responder {
    // Здесь вы должны получить список воркспейсов из базы данных для данного пользователя
    let workspaces = vec![]; // Предположим, что этот список получен из базы данных

    HttpResponse::Ok().json(workspaces)
}
