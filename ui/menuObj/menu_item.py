import pygame

class MenuItem:
    """A recursive menu item that can contain other menu items."""
    def __init__(self, label, action=None, children=None, font=None):
        self.label = label
        self.action = action  # String ID or function
        self.font = font
        
        # Initialize children: 
        # Converts tuple-based definitions (label, action, children) into MenuItem objects
        self.children = []
        if children:
            for c in children:
                if isinstance(c, MenuItem):
                    self.children.append(c)
                elif isinstance(c, tuple):
                    lbl = c[0]
                    act = c[1] if len(c) > 1 else None
                    sub = c[2] if len(c) > 2 else None
                    self.children.append(MenuItem(lbl, act, sub, font=font))
        
        # State
        self.is_hovered = False
        self.is_open = False
        
        # Layout (calculated during update_layout)
        self.rect = pygame.Rect(0, 0, 0, 0) # Hitbox relative to screen
        self.tw = 0
        self.th = 0
        self.submenu_width = 160
        self.submenu_height = 0

    def calculate_layout(self, x, y, is_horizontal, min_width=140):
        """Recursively calculate positions and widths."""
        tw, th = self.font.size(self.label)
        self.tw, self.th = tw, th
        
        if is_horizontal:
            self.rect = pygame.Rect(x, 0, tw + 24, 34)
        else:
            self.rect = pygame.Rect(x, y, min_width, 28 if self.label != "---" else 8)

        if self.children:
            max_child_w = min_width
            total_h = 0
            for child in self.children:
                ch_w, _ = self.font.size(child.label)
                if ch_w + 30 > max_child_w:
                    max_child_w = ch_w + 30
                total_h += (28 if child.label != "---" else 8)
            
            self.submenu_width = max_child_w
            self.submenu_height = total_h
            
            child_y = self.rect.bottom if is_horizontal else self.rect.top
            child_x = self.rect.left if is_horizontal else self.rect.right
            
            curr_y = child_y
            for child in self.children:
                child.calculate_layout(child_x, curr_y, False, min_width=max_child_w)
                curr_y += child.rect.height