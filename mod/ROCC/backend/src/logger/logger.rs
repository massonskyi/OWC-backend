use chrono::Local;
use colored::*;
use fern::Dispatch;
use log::{debug, error, info, warn, trace};
use std::path::Path;
use std::fs::OpenOptions;
use async_std::sync::Arc;

pub struct AsyncLogger{
    file_path: Arc<String>,
}


impl AsyncLogger{

    //* Create new struct AsyncLogger
    //*
    //* Params
    //* 
    //* 'log_file' - path to log file
    //*  
    //* Returned
    //*
    //* AsyncLogger object
    //* 
    //* ```
    //* let logger = AsyncLogger("path_to_log_file")
    //* ```
    pub fn new(log_file: &str) -> Self{
        AsyncLogger{
            file_path: Arc::new(log_file.to_string())
        }
    }

    //* Initialization logger
    //*
    //* Returned
    //*
    //* None or Error
    //* 
    //* ```
    //* let logger = AsyncLogger("path_to_log_file")
    //* logger.init.await()?
    //* ```
    pub async fn init(&self) -> Result<(), Box<dyn std::error::Error>>{
        let file_path = Arc::clone(&self.file_path);

        // async file open
        let file = OpenOptions::new()
        .create(true)
        .write(true)
        .append(true)
        .open(Path::new(&*file_path))?;


        // settings fern for async logs
        Dispatch::new()
        .format(|out, message, record|{
            let time = Local::now().format("%Y-%m-%d %H:%M:%S").to_string().purple();
            let level = record.level();
            let target = record.target().to_string().cyan();
            let msg = message.to_string().green();

            let colored_level = match level{
                log::Level::Error => level.to_string().red(),
                log::Level::Warn => level.to_string().yellow(),
                log::Level::Info => level.to_string().green(),
                log::Level::Debug => level.to_string().blue(),
                log::Level::Trace => level.to_string().purple(),
            };

            out.finish(format_args!(
                "{} [{}] {}: {}",
                time, colored_level, target, msg
            ));
        })
        .chain(std::io::stdout()) // input in console
        .chain(file)              // write in file
        .apply()?;

    Ok(())
    }

    //*Async functions logs for more level *//

    //* Logs function bInfo
    //*
    //* Params
    //* msg - string message to log
    //* 
    //* Returned
    //*
    //* None
    //* 
    //* ```
    //* let logger = AsyncLogger("path_to_log_file")
    //* logger.init.await()?
    //* logger.info('INFO MESSAGE') 
    //* ```
    pub async fn b_info(&self, msg: &str) {
        info!("{}", msg);
    }

    //* Logs function bWarn
    //*
    //* Params
    //* msg - string message to log
    //* 
    //* Returned
    //*
    //* None
    //* 
    //* ```
    //* let logger = AsyncLogger("path_to_log_file")
    //* logger.init.await()?
    //* logger.warn('WARN MESSAGE') 
    //* ```
    pub async fn b_warn(&self, msg: &str) {
        warn!("{}", msg);
    }

    //* Logs function bErr
    //*
    //* Params
    //* msg - string message to log
    //* 
    //* Returned
    //*
    //* None
    //* 
    //* ```
    //* let logger = AsyncLogger("path_to_log_file")
    //* logger.init.await()?
    //* logger.err('ERR MESSAGE') 
    //* ```
    pub async fn b_err(&self, msg: &str) {
        error!("{}", msg);
    }

    //* Logs function bDeb
    //*
    //* Params
    //* msg - string message to log
    //* 
    //* Returned
    //*
    //* None
    //* 
    //* ```
    //* let logger = AsyncLogger("path_to_log_file")
    //* logger.init.await()?
    //* logger.deb('DEBUG MESSAGE') 
    //* ```
    pub async fn b_deb(&self, msg: &str) {
        debug!("{}", msg);
    }

    //* Logs function bTrace
    //*
    //* Params
    //* msg - string message to log
    //* 
    //* Returned
    //*
    //* None
    //* 
    //* ```
    //* let logger = AsyncLogger("path_to_log_file")
    //* logger.init.await()?
    //* logger.trace('TRACE MESSAGE') 
    //* ```
    pub async fn b_trace(&self, msg: &str) {
        trace!("{}", msg);
    }

}