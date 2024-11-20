import gradio as gr

class UIManager:
    def __init__(self, data_processor, event_handler):
        self.data_processor = data_processor
        self.event_handler = event_handler
        self.css = """
    .container { 
        margin: 15px; 
        padding-bottom: 160px;  /* 여백 줄임 */
        position: relative;
    }
    .title { text-align: center; margin-bottom: 20px; }
    .chatbot { 
        height: 10000px !important;
    }
    .chatbot > div {
        height: 100% !important;
    }
    .footer { 
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background-color: white;
        padding: 15px;
        border-top: 1px solid #ddd;
        z-index: 1000;
        margin: 0;
    }
    .page-controls { 
        display: flex; 
        justify-content: center; 
        align-items: center; 
        gap: 10px;
        margin-bottom: 5px;
    }
    .page-controls button {
        min-width: 40px !important;
        height: 40px !important;
        padding: 0 !important;
    }
    .choice-buttons {
        position: fixed;
        bottom: 70px;  
        left: 0;
        right: 0;
        background-color: white;
        padding: 15px;
        z-index: 1000;
        margin: 0;
        border-top: 1px solid #ddd;
    }
    .model-buttons button {
        min-width: 150px !important;  /* 버튼 크기 조정 */
        height: 45px !important;
    }
    .cancel-button { 
        width: 120px !important;
        height: 35px !important;
        margin: 10px auto 0 auto;  /* 중앙 정렬 */
        display: block;
    }
    .statistics { 
        margin-top: 10px; 
        padding: 10px; 
        background-color: #e9ecef; 
        border-radius: 8px; 
        font-size: 0.9em; 
    }
        """
    
    def create_interface(self):
        with gr.Blocks(css=self.css) as iface:
            with gr.Column(elem_classes="container"):
                gr.Markdown("## 대화 비교 평가", elem_classes="title")
                
                with gr.Column(elem_classes="statistics"):
                    statistics = gr.Markdown("")
                
                with gr.Row():
                    outputs1 = gr.Chatbot(label="모델 A의 응답", elem_classes="chatbot")
                    outputs2 = gr.Chatbot(label="모델 B의 응답", elem_classes="chatbot")
                
                with gr.Column(elem_classes="choice-buttons"):
                    with gr.Row(elem_classes="model-buttons"):
                        left_button = gr.Button("◀ 모델 A 선택", variant="primary", scale=1)
                        right_button = gr.Button("모델 B 선택 ▶", variant="primary", scale=1)
                    cancel_button = gr.Button("선택 취소", variant="secondary", scale=1, elem_classes="cancel-button")
                
                with gr.Column(elem_classes="footer"):
                    with gr.Row(elem_classes="page-controls"):
                        prev_button = gr.Button("◀", scale=1)
                        current_page = gr.Markdown("현재 페이지: 1 / " + str(len(self.data_processor.df)))
                        next_button = gr.Button("▶", scale=1)
                    slider = gr.Slider(
                        minimum=0,
                        maximum=len(self.data_processor.df)-1,
                        step=1,
                        value=0,
                        label="",
                        visible=False
                    )
                    page_index = gr.State(0)
            
            # 초기 페이지 로드
            initial_outputs1, initial_outputs2, initial_page = self.event_handler.load_initial_page()
            outputs1.value = initial_outputs1
            outputs2.value = initial_outputs2
            current_page.value = initial_page
            
            # 이벤트 핸들러 연결
            slider.change(
                fn=self.event_handler.update_page,
                inputs=[slider],
                outputs=[outputs1, outputs2, page_index, current_page, 
                        left_button, right_button, cancel_button]
            )
            
            left_button.click(
                fn=self.event_handler.update_selection,
                inputs=[page_index, gr.State("left"), slider],
                outputs=[outputs1, outputs2, page_index, current_page,
                        left_button, right_button, cancel_button, slider, statistics]
            )

            right_button.click(
                fn=self.event_handler.update_selection,
                inputs=[page_index, gr.State("right"), slider],
                outputs=[outputs1, outputs2, page_index, current_page,
                        left_button, right_button, cancel_button, slider, statistics]
            )
                
            cancel_button.click(
                fn=self.event_handler.cancel_selection,
                inputs=[page_index, slider],
                outputs=[outputs1, outputs2, page_index, current_page,
                        left_button, right_button, cancel_button, slider]
            )
            
            prev_button.click(
                fn=self.event_handler.move_page,
                inputs=[page_index, gr.State(-1)],
                outputs=[outputs1, outputs2, page_index, current_page,
                        left_button, right_button, cancel_button, slider]
            )
            
            next_button.click(
                fn=self.event_handler.move_page,
                inputs=[page_index, gr.State(1)],
                outputs=[outputs1, outputs2, page_index, current_page,
                        left_button, right_button, cancel_button, slider]
            )

        return iface