import pygame
import os
import logging


class HelpPage:
    def __init__(self, client):
        self.logger = logging.getLogger(__name__)
        self.client = client
        self.is_german = self.client.is_german

        # parameters
        self.small_width, self.small_height = 800, 800
        self.darkgreen = 100, 150, 100
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)
        self.title_font = pygame.font.Font(None, 40)
        self.big_font = pygame.font.Font(None, 32)

        self.screen = pygame.display.set_mode((self.small_width, self.small_height))
        self.back_button = pygame.Rect(100, 700, 150, 40)
        caption_text = "Hilfe Seite" if self.is_german else "Help Page"
        pygame.display.set_caption(caption_text)
        self.content_list = self.parse_text()

        # Scrolling parameters
        self.scroll_offset = 0
        self.scroll_speed = 20
        self.max_scroll = self.calculate_max_scroll()

    def parse_text(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if self.is_german:
            rules_path = os.path.join(current_dir, "../game/rules_de.txt")
        else:
            rules_path = os.path.join(current_dir, "../game/rules_en.txt")
        with open(rules_path, "r", encoding="utf-8") as file:
            content = file.read()

        raw_lines = content.split("\n")
        parsed_lines = []
        for line in raw_lines:
            if line.startswith("## "):
                parsed_lines.append(("title", line[3:]))
            elif line.strip() == "---":
                parsed_lines.append(("line", ""))
            else:
                wrapped_lines = self.wrap_text(line, self.small_font, 700)
                for wrapped_line in wrapped_lines:
                    parsed_lines.append(("text", wrapped_line))
        return parsed_lines

    def calculate_max_scroll(self):
        scroll_height = 0
        for content_type, content, *extra in self.content_list:
            if content_type == "title":
                scroll_height += 40
            elif content_type == "text":
                scroll_height += 30
            elif content_type == "line":
                scroll_height += 20
        visible_area_height = 600
        max_scroll = max(0, scroll_height - visible_area_height)
        return max_scroll

    def wrap_text(self, text, font, max_width=700):
        if not text.strip():
            return []

        words = text.split(" ")
        wrapped_lines = []
        current_line = []
        current_width = 0
        for word in words:
            word_width, _ = font.size(word + " ")
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                wrapped_lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width
        if current_line:
            wrapped_lines.append(" ".join(current_line))
        return wrapped_lines

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Back button
            if self.back_button.collidepoint(event.pos):
                self.logger.info("Returning to the game list page...")
                return "back"

        if event.type == pygame.MOUSEWHEEL:
            self.scroll_offset -= event.y * self.scroll_speed
            self.scroll_offset = max(0, min(self.scroll_offset, self.max_scroll))
        return None

    def render(self):
        self.screen.fill("white")

        # Title
        title_text = (
            "Hilfe - Hanabi Regeln" if self.is_german else "Help - Hanabi Rules"
        )
        title = self.title_font.render(title_text, True, self.darkgreen)
        title_width = title.get_width()
        center_x = (self.small_width - title_width) // 2
        self.screen.blit(title, (center_x, 20))

        # Text
        y_position = 80
        for content_type, content in self.content_list:
            y_position_display = (
                y_position - self.scroll_offset
            )  # Ad just for scrolling
            if 80 <= y_position_display <= 650:
                if content_type == "title":
                    title_surface = self.big_font.render(content, True, "black")
                    self.screen.blit(title_surface, (50, y_position_display))
                    y_position += 40
                elif content_type == "text":
                    text_surface = self.small_font.render(content, True, "black")
                    self.screen.blit(text_surface, (50, y_position_display))
                    y_position += 30
                elif content_type == "line":
                    pygame.draw.line(
                        self.screen,
                        "black",
                        (50, y_position_display),
                        (750, y_position_display),
                        1,
                    )
                    y_position += 20
            else:
                if content_type == "title":
                    y_position += 40
                elif content_type == "text":
                    y_position += 30
                elif content_type == "separator":
                    y_position += 20

        # Button
        pygame.draw.rect(self.screen, (200, 50, 50), self.back_button)
        back_text = "Zurück" if self.is_german else "Back"
        back_surface = self.small_font.render(back_text, True, "white")
        self.screen.blit(
            back_surface, (self.back_button.x + 50, self.back_button.y + 10)
        )
