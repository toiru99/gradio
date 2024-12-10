import gradio as gr

class UIManager:
    def __init__(self, data_processor, event_handler):
        self.data_processor = data_processor
        self.event_handler = event_handler
        self.css = """
        <style>
        .container { 
            margin: 15px; 
            padding: 15px;
            display: flex;
            flex-direction: column;
            height: 100vh;
        }
        .chatbot { 
            flex: 1; /* 부모 요소의 남은 공간을 모두 차지하도록 설정 */
            overflow-y: auto !important;
        }
        .bottom-controls {
            background-color: white;
            padding: 15px;
            border-top: 1px solid #ddd;
            margin-top: 20px;
        }
        .page-controls { 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            gap: 10px;
            margin: 15px 0;
        }
        .statistics { 
            margin-bottom: 15px; 
            padding: 10px; 
            background-color: #e9ecef; 
            border-radius: 8px; 
        }
        .bottom-controls button {
            background-color: #FF5722; /* 더 진한 주황색으로 변경 */
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .bottom-controls button:hover {
            background-color: #E64A19; /* 더 진한 주황색의 어두운 색상으로 변경 */
        }
        .bottom-controls button:disabled {
            background-color: #ccc;
            cursor: not-allowed;
        }
        .bottom-controls button.selected {
            background-color: #4caf50; /* 선택된 버튼의 색상 (녹색) */
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
                # 상단: 세션 선택
                with gr.Row():
                    session_dropdown = gr.Dropdown(
                        choices=["세션 1", "세션 2", "세션 3", "세션 4"],
                        value="세션 1",
                        label="세션 선택"
                    )
                                                                
                # 중단: 대화창 - 동적 라벨 적용
                with gr.Row():
                    with gr.Column(elem_classes="chatbot"):
                        outputs1 = gr.Chatbot(label="모델 1의 응답", elem_classes="chatbot")
                    with gr.Column(elem_classes="chatbot"):
                        outputs2 = gr.Chatbot(label="모델 2의 응답", elem_classes="chatbot")
                
                # 하단: 선택 버튼들
                with gr.Column(elem_classes="bottom-controls"):
                    with gr.Column():
                        gr.Markdown("### 툴 평가")
                        with gr.Row():
                            button_1_up = gr.Button("모델 1 툴 good")
                            button_1_down = gr.Button("모델 1 툴 bad")
                            button_2_up = gr.Button("모델 2 툴 good")
                            button_2_down = gr.Button("모델 2 툴 bad")
                        
                        gr.Markdown("### 가장 좋은 대답한 모델")
                        with gr.Row():
                            best_1 = gr.Button("모델 1")
                            best_2 = gr.Button("모델 2")
                        
                        # gr.Markdown("### 가장 나쁜 대답한 모델")
                        # with gr.Row():
                        #     worst_1 = gr.Button("모델 1")
                        #     worst_2 = gr.Button("모델 2")
                        
                        gr.Markdown("### 모델들이 비슷할 경우")
                        with gr.Row():
                            neutral_button = gr.Button("중립 (모델들이 비슷)")
                        
                        cancel_button = gr.Button("선택 취소")
                    
                    with gr.Column():
                        with gr.Row(elem_classes="page-controls"):
                            prev_button = gr.Button("◀", scale=1)
                            current_page = gr.Markdown("현재 페이지: 1 / " + str(len(self.data_processor.df)))
                            next_button = gr.Button("▶", scale=1)
                            
                        slider = gr.Slider(
                            minimum=1,
                            maximum=len(self.data_processor.df),
                            step=1,
                            value=1,
                            label="페이지 선택",
                            visible=True
                        )
                        page_index = gr.State(0)

                # 상단: 통계
                with gr.Column(elem_classes="statistics"):
                    statistics = gr.Markdown("")

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
                            best_1, best_2,cancel_button,
                            button_1_up, button_1_down, button_2_up, button_2_down]
                )
                
                best_1.click(
                    fn=self.event_handler.update_model_vote,
                    inputs=[page_index, gr.State("1"), gr.State("best")],
                    outputs=[outputs1, outputs2, page_index, current_page,
                            best_1, best_2, cancel_button,
                            button_1_up, button_1_down, button_2_up, button_2_down, 
                            slider, statistics]
                )
                
                best_2.click(
                    fn=self.event_handler.update_model_vote,
                    inputs=[page_index, gr.State("2"), gr.State("best")],
                    outputs=[outputs1, outputs2, page_index, current_page,
                            best_1, best_2, cancel_button,
                            button_1_up, button_1_down, button_2_up, button_2_down, 
                            slider, statistics]
                )
                
                
                neutral_button.click(
                    fn=self.event_handler.update_model_vote,
                    inputs=[page_index, gr.State("N"), gr.State("neutral")],
                    outputs=[outputs1, outputs2, page_index, current_page,
                            best_1, best_2, cancel_button,
                            button_1_up, button_1_down, button_2_up, button_2_down, 
                            slider, statistics]
                )
                
                cancel_button.click(
                    fn=self.event_handler.cancel_selection,
                    inputs=[page_index, slider],
                    outputs=[outputs1, outputs2, page_index, current_page,
                            best_1, best_2, cancel_button,
                            button_1_up, button_1_down, button_2_up, button_2_down, 
                            slider, statistics]
                )
                
                prev_button.click(
                    fn=self.event_handler.move_page,
                    inputs=[page_index, gr.State(-1)],
                    outputs=[outputs1, outputs2, page_index, current_page, 
                            best_1, best_2, cancel_button,
                            button_1_up, button_1_down, button_2_up, button_2_down, slider]
                )
                

                next_button.click(
                    fn=self.event_handler.move_page,
                    inputs=[page_index, gr.State(1)],
                    outputs=[outputs1, outputs2, page_index, current_page, 
                            best_1, best_2, cancel_button,
                            button_1_up, button_1_down, button_2_up, button_2_down, slider]
                )

                # 툴 평가 버튼 이벤트 연결
                button_1_up.click(
                    fn=self.event_handler.update_tool_vote,
                    inputs=[page_index, gr.State(1), gr.State("up")],
                    outputs=[outputs1, outputs2, page_index, current_page,
                            best_1, best_2, cancel_button,
                            button_1_up, button_1_down, button_2_up, button_2_down,
                            slider, statistics]
                )
                
                button_1_down.click(
                    fn=self.event_handler.update_tool_vote,
                    inputs=[page_index, gr.State(1), gr.State("down")],
                    outputs=[outputs1, outputs2, page_index, current_page,
                            best_1, best_2, cancel_button,
                            button_1_up, button_1_down, button_2_up, button_2_down,
                            slider, statistics]
                )
                
                button_2_up.click(
                    fn=self.event_handler.update_tool_vote,
                    inputs=[page_index, gr.State(2), gr.State("up")],
                    outputs=[outputs1, outputs2, page_index, current_page,
                            best_1, best_2, cancel_button,
                            button_1_up, button_1_down, button_2_up, button_2_down,
                            slider, statistics]
                )
                
                button_2_down.click(
                    fn=self.event_handler.update_tool_vote,
                    inputs=[page_index, gr.State(2), gr.State("down")],
                    outputs=[outputs1, outputs2, page_index, current_page,
                            best_1, best_2, cancel_button,
                            button_1_up, button_1_down, button_2_up, button_2_down,
                            slider, statistics]
                )
                
                # 세션 변경 이벤트 핸들러 연결
                session_dropdown.change(
                    fn=self.event_handler.change_session,
                    inputs=[session_dropdown],
                    outputs=[outputs1, outputs2, page_index, current_page,
                            best_1, best_2, cancel_button,
                            button_1_up, button_1_down, button_2_up, button_2_down, 
                            slider, statistics]
                )

        return iface