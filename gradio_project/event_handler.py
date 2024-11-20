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
            self.data_processor.display_conversations(file_content2),
            current_page
        )

    def update_page(self, page_index):
        file_content1 = self.data_processor.df['data1'][page_index]
        file_content2 = self.data_processor.df['data2'][page_index]
        current_page = f"현재 페이지: {page_index + 1} / {len(self.data_processor.df)}"
        
        left_disabled = bool(self.data_processor.df['left'][page_index] > 0 or 
                           self.data_processor.df['right'][page_index] > 0)
        right_disabled = left_disabled
        cancel_disabled = not left_disabled
        
        return (
            self.data_processor.display_conversations(file_content1),
            self.data_processor.display_conversations(file_content2),
            page_index,
            current_page,
            gr.Button(interactive=not left_disabled),
            gr.Button(interactive=not right_disabled),
            gr.Button(interactive=not cancel_disabled)
        )

    def update_selection(self, page_index, choice, slider):
        if choice == "left":
            self.data_processor.df.at[page_index, 'left'] += 1
        elif choice == "right":
            self.data_processor.df.at[page_index, 'right'] += 1
        
        self.data_processor.save_votes()
        next_page = min(page_index + 1, len(self.data_processor.df) - 1)
        
        if (next_page == len(self.data_processor.df) - 1 and 
            (self.data_processor.df.at[page_index, 'left'] > 0 or 
            self.data_processor.df.at[page_index, 'right'] > 0)):
            stats = self.data_processor.calculate_statistics()
            return self.update_page(next_page) + (next_page,) + (stats,) + (True,)
        
        return self.update_page(next_page) + (next_page,) + ("",) + (True,)

    def cancel_selection(self, page_index, slider):
        self.data_processor.df.at[page_index, 'left'] = max(0, self.data_processor.df.at[page_index, 'left'] - 1)
        self.data_processor.df.at[page_index, 'right'] = max(0, self.data_processor.df.at[page_index, 'right'] - 1)
        self.data_processor.save_votes()
        
        return self.update_page(page_index) + (page_index,)

    def move_page(self, page_index, direction):
        new_page = max(0, min(len(self.data_processor.df) - 1, page_index + direction))
        return self.update_page(new_page) + (new_page,)