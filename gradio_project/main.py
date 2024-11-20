from data_processor import DataProcessor
from event_handler import EventHandler
from ui_manager import UIManager
import gradio as gr

def create_interface(port):
    data_processor = DataProcessor('output.csv', port)
    event_handler = EventHandler(data_processor)
    ui_manager = UIManager(data_processor, event_handler)
    
    interface = ui_manager.create_interface()
    interface.queue()
    interface.launch(
        server_name="0.0.0.0",
        server_port=port,
        share=True,
        prevent_thread_lock=True
    )

def main():
    ports = [7860, 7861, 7862]
    for port in ports:
        create_interface(port)
    
    # 프로그램이 종료되지 않도록 대기
    input("Press Enter to exit...")

if __name__ == "__main__":
    main()