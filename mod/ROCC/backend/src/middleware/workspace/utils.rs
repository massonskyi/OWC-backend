pub struct WorkspaceUtils;


impl WorkspaceUtils {
    pub fn user_has_access(user: &UserModel, workspace: &WorkspaceModel) -> bool {
        user.id == workspace.owner_id
    }

    pub fn generate_unique_container_id() -> String {
        // Логика для генерации уникального ID контейнера
        "unique_container_id".to_string()
    }
}