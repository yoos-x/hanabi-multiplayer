import logging
import pygame

pygame.init()


class LoginPage:
    def __init__(self, client):
        self.logger = logging.getLogger(__name__)
        # parameters
        self.small_width, self.small_height = 800, 800

        self.client = client
        self.screen = pygame.display.set_mode((self.small_width, self.small_height))

        # UI elements
        self.name_input = pygame.Rect(250, 200, 400, 40)
        self.ip_input = pygame.Rect(250, 300, 400, 40)
        self.port_input = pygame.Rect(250, 400, 400, 40)
        self.connect_button = pygame.Rect(500, 500, 50, 50)
        self.quit_button = pygame.Rect(300, 500, 50, 50)

        self.input_active = False
        self.active_input = None
        self.username = ""
        self.server_ip = ""
        self.server_port = ""

        # Colors and fonts
        self.lightgreen = 175, 200, 175
        self.font = pygame.font.Font(None, 28)
        self.title_font = pygame.font.Font(None, 40)

    def try_connect(self):
        self.client.username = self.username.strip()
        self.client.server_ip = self.server_ip.strip()
        self.client.server_port = self.server_port.strip()

        # Reset input fields if connection fails
        if (
            self.client.username
            and self.client.server_ip
            and self.client.server_port.isdigit()
        ):
            if self.client.connect_to_server(self.server_ip, int(self.server_port)):
                return "lobby"
            else:
                # Clear IP and port fields on failed connection
                self.server_ip = ""
                self.server_port = ""
                self.active_input = "server_ip"  # Set focus to IP field
        return None

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.name_input.collidepoint(event.pos):
                self.active_input = "username"
            elif self.ip_input.collidepoint(event.pos):
                self.active_input = "server_ip"
            elif self.port_input.collidepoint(event.pos):
                self.active_input = "server_port"
            elif self.connect_button.collidepoint(event.pos):
                return self.try_connect()
            elif self.quit_button.collidepoint(event.pos):
                return "quit"

        elif event.type == pygame.KEYDOWN:
            if self.active_input == "username":
                if event.key == pygame.K_BACKSPACE:
                    self.username = self.username[:-1]
                elif event.key == pygame.K_RETURN:
                    return self.try_connect()
                else:
                    self.username += event.unicode
            elif self.active_input == "server_ip":
                if event.key == pygame.K_BACKSPACE:
                    self.server_ip = self.server_ip[:-1]
                elif event.key == pygame.K_RETURN:
                    return self.try_connect()
                else:
                    self.server_ip += event.unicode
            elif self.active_input == "server_port":
                if event.key == pygame.K_BACKSPACE:
                    self.server_port = self.server_port[:-1]
                elif event.key == pygame.K_RETURN:
                    return self.try_connect()
                else:
                    self.server_port += event.unicode
        return None

    def render(self):
        self.screen.fill(self.lightgreen)

        # Title
        title = self.title_font.render("Hanabi - Login", True, "white")
        title_width = title.get_width()
        center_x = (self.small_width - title_width) // 2
        self.screen.blit(title, (center_x, 50))

        # Input boxes
        name_border_width = 4 if self.active_input == "username" else 2
        ip_border_width = 4 if self.active_input == "server_ip" else 2
        port_border_width = 4 if self.active_input == "server_port" else 2

        pygame.draw.rect(self.screen, "white", self.name_input, name_border_width)
        pygame.draw.rect(self.screen, "white", self.ip_input, ip_border_width)
        pygame.draw.rect(self.screen, "white", self.port_input, port_border_width)
        username_text = self.font.render(self.username, True, "black")
        server_ip_text = self.font.render(self.server_ip, True, "black")
        server_port_text = self.font.render(self.server_port, True, "black")
        self.screen.blit(username_text, (self.name_input.x + 5, self.name_input.y + 10))
        self.screen.blit(server_ip_text, (self.ip_input.x + 5, self.ip_input.y + 10))
        self.screen.blit(
            server_port_text, (self.port_input.x + 5, self.port_input.y + 10)
        )
        pygame.draw.rect(self.screen, "white", self.port_input, 2)

        # Input field labels
        name_label = self.font.render("Name:", True, "white")
        ip_label = self.font.render("Server IP:", True, "white")
        port_label = self.font.render("Port:", True, "white")
        self.screen.blit(name_label, (130, 210))
        self.screen.blit(ip_label, (130, 310))
        self.screen.blit(port_label, (130, 410))

        # Connect button
        pygame.draw.rect(self.screen, (0, 128, 0), self.connect_button)
        arrow_x1 = self.connect_button.x + 10
        arrow_x2 = self.connect_button.x + 40
        arrow_y = self.connect_button.y + self.connect_button.height // 2
        pygame.draw.line(
            self.screen, "white", (arrow_x1, arrow_y), (arrow_x2, arrow_y), 3
        )
        pygame.draw.line(
            self.screen, "white", (arrow_x2, arrow_y), (arrow_x2 - 10, arrow_y - 10), 3
        )
        pygame.draw.line(
            self.screen, "white", (arrow_x2, arrow_y), (arrow_x2 - 10, arrow_y + 10), 3
        )

        # quit button
        pygame.draw.rect(self.screen, (220, 50, 50), self.quit_button)
        x_center_x = self.quit_button.x + self.quit_button.width // 2
        x_center_y = self.quit_button.y + self.quit_button.height // 2
        pygame.draw.line(
            self.screen,
            "white",
            (x_center_x - 10, x_center_y - 10),
            (x_center_x + 10, x_center_y + 10),
            3,
        )
        pygame.draw.line(
            self.screen,
            "white",
            (x_center_x + 10, x_center_y - 10),
            (x_center_x - 10, x_center_y + 10),
            3,
        )
