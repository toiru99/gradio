import gradio as gr

class EventHandler:
    def __init__(self, data_processor):
        self.data_processor = data_processor
    
    def load_initial_page(self):
        file_content1 = self.data_processor.df['data1'][0]
        file_content2 = self.data_processor.df['data2'][0]
        current_page = f"현재 페이지: 1 / {len(self.data_processor.df)}"
        return (
            self.data_processor.display_conversations(file_content1),
            self.data_processor.display_conversations_refactored(file_content2),
            current_page
        )

    def update_page(self, page_index):
        file_content1 = self.data_processor.df['data1'][page_index]
        file_content2 = self.data_processor.df['data2'][page_index]
        current_page = f"현재 페이지: {page_index + 1} / {len(self.data_processor.df)}"
        
        buttons_disabled = bool(self.data_processor.df['left'][page_index] > 0 or 
                        self.data_processor.df['right'][page_index] > 0 or
                        self.data_processor.df['neutral'][page_index] > 0)  # 중립 추가
        
        return (
            self.data_processor.display_conversations(file_content1),
            self.data_processor.display_conversations_refactored(file_content2),
            page_index,
            current_page,
            gr.Button(interactive=not buttons_disabled),
            gr.Button(interactive=not buttons_disabled),
            gr.Button(interactive=not buttons_disabled),  # 중립 버튼
            gr.Button(interactive=not not buttons_disabled)  # 취소 버튼
        )

    def update_selection(self, page_index, choice, slider):
        if choice == "left":
            self.data_processor.df.at[page_index, 'left'] += 1
        elif choice == "right":
            self.data_processor.df.at[page_index, 'right'] += 1
        elif choice == "neutral":  # 중립 선택 추가
            self.data_processor.df.at[page_index, 'neutral'] += 1

        self.data_processor.save_votes()
        
        # 현재 페이지에 머무르도록 next_page를 현재 page_index로 설정
        next_page = page_index
        
        stats = self.data_processor.calculate_statistics()
        return self.update_page(next_page) + (next_page,) + (stats,) + (True,)

    def cancel_selection(self, page_index, slider):
        self.data_processor.df.at[page_index, 'left'] = max(0, self.data_processor.df.at[page_index, 'left'] - 1)
        self.data_processor.df.at[page_index, 'right'] = max(0, self.data_processor.df.at[page_index, 'right'] - 1)
        self.data_processor.df.at[page_index, 'neutral'] = max(0, self.data_processor.df.at[page_index, 'neutral'] - 1)
        self.data_processor.save_votes()
        
        # 툴 평가도 초기화
        self.data_processor.df.at[page_index, 'model1_up'] = 0
        self.data_processor.df.at[page_index, 'model1_down'] = 0
        self.data_processor.df.at[page_index, 'model2_up'] = 0
        self.data_processor.df.at[page_index, 'model2_down'] = 0
        self.data_processor.save_votes()
        
        # 통계 업데이트
        stats = self.data_processor.calculate_statistics()
        
        return self.update_page(page_index) + (page_index,) + (stats,) + (True,)

    def move_page(self, page_index, direction):
        new_page = max(0, min(len(self.data_processor.df) - 1, page_index + direction))
        return self.update_page(new_page) + (new_page,)

    def update_tool_vote(self, page_index, model_num, vote_type):
        # 이전 선택 초기화
        opposite_vote = "down" if vote_type == "up" else "up"
        self.data_processor.df.at[page_index, f'model{model_num}_{opposite_vote}'] = 0
        
        # 새로운 선택 기록
        column_name = f'model{model_num}_{vote_type}'
        self.data_processor.df.at[page_index, column_name] = 1
        self.data_processor.save_votes()
        
        # 통계 업데이트
        stats = self.data_processor.calculate_statistics()
        
        # 버튼 상태 업데이트
        button_states = []
        for m in [1, 2]:
            for v in ["up", "down"]:
                if m == model_num and v == vote_type:
                    text = f"모델 {'A' if m==1 else 'B'} 툴 {'good' if v=='up' else 'bad'} (선택됨)"
                    interactive = False
                else:
                    text = f"모델 {'A' if m==1 else 'B'} 툴 {'good' if v=='up' else 'bad'}"
                    interactive = True
                button_states.append(gr.Button(value=text, interactive=interactive))
        
        button_states.append(stats)
        return tuple(button_states)