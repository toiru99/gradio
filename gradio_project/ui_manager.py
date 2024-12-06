import gradio as gr

class UIManager:
    def __init__(self, data_processor, event_handler):
        self.data_processor = data_processor
        self.event_handler = event_handler
        self.css = """
        <style>
        .container { 
            margin: 15px; 
            padding-bottom: 20px; 
            position: relative;
        }
        .title { 
            text-align: center; 
            margin-bottom: 20px; 
        }
        .chatbot { 
            height: auto !important;
            overflow-y: visible !important;
            margin-bottom: 20px !important;
        }
        .chatbot > div {
            height: auto !important;
            overflow-y: visible !important;
        }
        .chatbot > div > div {
            overflow-y: visible !important;
            max-height: none !important;
        }
        
        .page-controls { 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            gap: 10px;
            margin: 20px 0;
            padding: 15px;
            border-top: 1px solid #ddd;
        }
        
        .page-controls button {
            min-width: 40px !important;
            height: 40px !important;
            padding: 0 !important;
        }
        
        .model-buttons {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 10px 0;
        }
        
        .tool-buttons {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin: 10px 0;
        }
        
        .statistics { 
            margin-top: 10px; 
            padding: 10px; 
            background-color: #e9ecef; 
            border-radius: 8px; 
            font-size: 0.9em; 
        }
        
        </style>
        """
        self.js = """
        function scrollToTop() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
            return [];
        }
        """
        
    def create_interface(self):
        with gr.Blocks(css=self.css, js=self.js) as iface:
            with gr.Column(elem_classes="container"):
                gr.Markdown("## 대화 비교 평가", elem_classes="title")
                
                with gr.Row():
                    outputs1 = gr.Chatbot(label="모델 A의 응답", elem_classes="chatbot")
                    outputs2 = gr.Chatbot(label="모델 B의 응답", elem_classes="chatbot")
                
                with gr.Column():
                    gr.Markdown("### 툴 평가")
                    with gr.Row(elem_classes="tool-buttons"):
                        model1_up = gr.Button("모델 A 툴 good")
                        model1_down = gr.Button("모델 A 툴 bad")
                        model2_up = gr.Button("모델 B 툴 good")
                        model2_down = gr.Button("모델 B 툴 bad")
                
                    with gr.Row(elem_classes="model-buttons"):
                        left_button = gr.Button("모델 A의 응답", variant="primary")
                        neutral_button = gr.Button("중립", variant="primary")
                        right_button = gr.Button("모델 B의 응답", variant="primary")
                    cancel_button = gr.Button("선택 취소", variant="primary")
                
                # 통계를 페이지 컨트롤 바로 위로 이동
                with gr.Column(elem_classes="statistics"):
                    statistics = gr.Markdown("")
                
                with gr.Column():
                    with gr.Row(elem_classes="page-controls"):
                        prev_button = gr.Button("◀")
                        current_page = gr.Markdown("현재 페이지: 1 / " + str(len(self.data_processor.df)))
                        next_button = gr.Button("▶")
                        slider = gr.Slider(
                            minimum=0,
                            maximum=len(self.data_processor.df)-1,
                            step=1,
                            value=0,
                            label="페이지 선택",
                            visible=True
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
                        left_button, right_button, neutral_button, cancel_button],
            )
            
            left_button.click(
                fn=self.event_handler.update_selection,
                inputs=[page_index, gr.State("left"), slider],
                outputs=[outputs1, outputs2, page_index, current_page,
                        left_button, right_button, neutral_button, cancel_button, slider, statistics]
            )

            right_button.click(
                fn=self.event_handler.update_selection,
                inputs=[page_index, gr.State("right"), slider],
                outputs=[outputs1, outputs2, page_index, current_page,
                        left_button, right_button, neutral_button, cancel_button, slider, statistics]
            )

            neutral_button.click(
                fn=self.event_handler.update_selection,
                inputs=[page_index, gr.State("neutral"), slider],
                outputs=[outputs1, outputs2, page_index, current_page,
                        left_button, right_button, neutral_button, cancel_button, slider, statistics]
            )
                
            cancel_button.click(
                fn=self.event_handler.cancel_selection,
                inputs=[page_index, slider],
                outputs=[outputs1, outputs2, page_index, current_page,
                        left_button, right_button, neutral_button, cancel_button, slider, statistics]
            )
            
            prev_button.click(
                fn=self.event_handler.move_page,
                inputs=[page_index, gr.State(-1)],
                outputs=[outputs1, outputs2, page_index, current_page,
                        left_button, right_button, neutral_button, cancel_button, slider],
                js="async () => { window.scrollTo({top: 0, behavior: 'auto'}); }"
            )
            
            next_button.click(
                fn=self.event_handler.move_page,
                inputs=[page_index, gr.State(1)],
                outputs=[outputs1, outputs2, page_index, current_page,
                        left_button, right_button, neutral_button, cancel_button, slider],
                js="async () => { window.scrollTo({top: 0, behavior: 'auto'}); }"
            )

            # 툴 평가 이벤트 핸들러 연결
            model1_up.click(
                fn=self.event_handler.update_tool_vote,
                inputs=[page_index, gr.State(1), gr.State("up")],
                outputs=[model1_up, model1_down, model2_up, model2_down, statistics]
            )
            
            model1_down.click(
                fn=self.event_handler.update_tool_vote,
                inputs=[page_index, gr.State(1), gr.State("down")],
                outputs=[model1_up, model1_down, model2_up, model2_down, statistics]
            )
            
            model2_up.click(
                fn=self.event_handler.update_tool_vote,
                inputs=[page_index, gr.State(2), gr.State("up")],
                outputs=[model1_up, model1_down, model2_up, model2_down, statistics]
            )
            
            model2_down.click(
                fn=self.event_handler.update_tool_vote,
                inputs=[page_index, gr.State(2), gr.State("down")],
                outputs=[model1_up, model1_down, model2_up, model2_down, statistics]
            )

        return iface