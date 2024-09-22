use serde::{Serialize, Deserialize};

#[derive(Serialize, Deserialize, Debug)]
pub struct WorkspaceModel {
    pub id: i32,
    pub name: String,
    pub description: Option<String>,
    pub owner_id: i32,
    pub created_at: String,
    pub updated_at: String,
    pub deleted_at: Option<String>,
    pub file_system: FileSystemModel,        // Файловая система
    pub docker_container: DockerContainerModel, // Docker-контейнер
    pub editors: Vec<CodeEditorModel>,       // Редакторы кода
    pub notes: Vec<NoteModel>,               // Модуль заметок
}

impl Clone for WorkspaceModel {
    fn clone(&self) -> Self {
        Self {
            id: self.id.clone(),
            name: self.name.clone(),
            description: self.description.clone(),
            owner_id: self.owner_id.clone(),
            created_at: self.created_at.clone(),
            updated_at: self.updated_at.clone(),
            deleted_at: self.deleted_at.clone(),
            file_system: self.file_system.clone(),
            docker_container: self.docker_container.clone(),
            editors: self.editors.clone(),
            notes: self.notes.clone(),
        }
    }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct FileModel {
    pub name: String,
    pub content: String,
    pub file_type: String, // Тип файла (например, текст, изображение и т.д.)
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct DirectoryModel {
    pub name: String,
    pub files: Vec<FileModel>,
    pub directories: Vec<DirectoryModel>,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct FileSystemModel {
    pub root: DirectoryModel,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct DockerContainerModel {
    pub container_id: String,
    pub image: String,  // Например, "rust:latest"
    pub status: String, // Статус контейнера (например, "running", "stopped")
    pub ports: Vec<String>, // Список открытых портов
}

impl DockerContainerModel {
    pub fn start_container(&mut self) {
        // Логика запуска контейнера через Docker API
        self.status = "running".to_string();
    }

    pub fn stop_container(&mut self) {
        // Логика остановки контейнера через Docker API
        self.status = "stopped".to_string();
    }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct CodeEditorModel {
    pub language: String, // Например, "Rust", "Python", "JavaScript"
    pub file: FileModel,
}

impl CodeEditorModel {
    pub fn save_file(&mut self, new_content: String) {
        self.file.content = new_content;
        // Логика сохранения файла
    }
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct NoteModel {
    pub id: i32,
    pub title: String,
    pub content: String,
    pub created_at: String,
    pub updated_at: String,
}