from gradio_project.data_processor import DataProcessor
from gradio_project.event_handler import EventHandler
from gradio_project.ui_manager import UIManager
import gradio as gr

def create_interface():
    # 기본 세션으로 1번 세션 사용
    data_processor = DataProcessor('output.csv', session=1)
    event_handler = EventHandler(data_processor)
    ui_manager = UIManager(data_processor, event_handler)
    
    interface = ui_manager.create_interface()
    interface.queue()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7869,
        share=True,
        prevent_thread_lock=True,
    )
    return interface

def main():
    create_interface()
    
    # 프로그램이 종료되지 않도록 대기  
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()