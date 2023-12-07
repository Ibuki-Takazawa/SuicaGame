import pygame
import pymunk
import pymunk.pygame_util
import random

pygame.init()
width, height = 1280, 720
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("Suica Game")
clock = pygame.time.Clock()
space = pymunk.Space()
space.gravity = (0, 900)
draw_options = pymunk.pygame_util.DrawOptions(screen)
draw_options.flags = pymunk.SpaceDebugDrawOptions.DRAW_SHAPES
ball_position_x = width // 2
ball_position_y = 50
ball_ready_to_drop = False
ball = None
ball_shape = None
game_over = False

WHITE = (255, 255, 255)
BOX_LINE_COLOR = (0, 0, 0)
BOX_LINE_WIDTH = 2

running = True
ball_sizes = [i for i in range(20, 170, 15)]
ball_colors = [
    (255, 0, 0),
    (255, 153, 0),
    (255, 255, 0),
    (51, 255, 0),
    (115, 255, 171),
    (0, 255, 255),
    (51, 133, 255),
    (51, 0, 255),
    (204, 0, 255),
    (255, 0, 153),
]

def create_ball(space, position, size_index):
    mass = 1
    radius = ball_sizes[size_index]
    color = ball_colors[size_index]
    moment = pymunk.moment_for_circle(mass, 0, radius)
    body = pymunk.Body(mass, moment)
    body.position = position
    shape = pymunk.Circle(body, radius)
    shape.elasticity = 0.5
    shape.friction = 0.5
    shape.collision_type = size_index + 1
    shape.color = ball_colors[size_index]
    space.add(body, shape)
    return shape

def create_static_ball(space, position, size_index):
    global radius
    radius = ball_sizes[size_index]
    color = ball_colors[size_index]
    body = pymunk.Body(body_type=pymunk.Body.STATIC)
    body.position = position
    shape = pymunk.Circle(body, radius)
    shape.elasticity = 0.5
    shape.friction = 0.5
    shape.collision_type = size_index + 1
    shape.color = ball_colors[size_index]
    space.add(body, shape)
    return shape

def make_ball_dynamic(ball_shape):
    space.remove(ball_shape, ball_shape.body)
    mass = 1
    radius = ball_shape.radius
    moment = pymunk.moment_for_circle(mass, 0, radius, (0, 0))

    ball_shape.body.body_type = pymunk.Body.DYNAMIC
    ball_shape.body.mass = mass
    ball_shape.body.moment = moment

    space.add(ball_shape.body, ball_shape)


def remove_ball_safe(space, shape):
    if shape.body in space.bodies:
        space.remove(shape, shape.body)

def combine_balls(space, arbiter):
    shape1, shape2 = arbiter.shapes
    size_index = shape1.collision_type -1

    if size_index < len(ball_sizes) - 1:
        new_size_index = size_index + 1
        position = (shape1.body.position + shape2.body.position) / 2
        remove_ball_safe(space, shape1)
        remove_ball_safe(space, shape2)
        create_ball(space, position, new_size_index)
    else:
        remove_ball_safe(space, shape1)
        remove_ball_safe(space, shape2)

def ball_collision_handler(arbiter, space, data):
    shape1, shape2 = arbiter.shapes

    if shape1.body.body_type == pymunk.Body.STATIC or shape2.body.body_type == pymunk.Body.STATIC:
        return False
    
    if shape1.collision_type == 0 or shape2.collision_type == 0:
        return False

    if arbiter.is_first_contact and shape1.collision_type == shape2.collision_type:
        space.add_post_step_callback(combine_balls, arbiter)

    return False

handler = space.add_default_collision_handler()
handler.post_solve = ball_collision_handler

def create_box(space, screen_width, screen_height, box_width, box_height):
    global floor
    left = (screen_width - box_width) / 2
    top = (screen_height - box_height) / 2
    right = left + box_width
    bottom = top + box_height

    floor = pymunk.Segment(space.static_body, (left, bottom), (right, bottom), 1)
    left_wall = pymunk.Segment(space.static_body, (left, top), (left, bottom), 1)
    right_wall = pymunk.Segment(space.static_body, (right, top), (right, bottom), 1)

    floor.collision_type = 0
    left_wall.collision_type = 0
    right_wall.collision_type = 0

    for line in [floor, left_wall, right_wall]:
        line.elasticity = 0.5
        line.friction = 0.5
        space.add(line)

box_width, box_height = 600, 600
create_box(space, width, height, box_width, box_height)

def draw_box(screen, left, top, box_width, box_height):
    right = left + box_width
    bottom = top + box_height

    pygame.draw.line(screen, BOX_LINE_COLOR, (left, bottom), (right, bottom), BOX_LINE_WIDTH)  # 下辺
    pygame.draw.line(screen, BOX_LINE_COLOR, (left, top), (left, bottom), BOX_LINE_WIDTH)  # 左辺
    pygame.draw.line(screen, BOX_LINE_COLOR, (right, top), (right, bottom), BOX_LINE_WIDTH)  # 右辺

def create_new_ball():
    global ball_shape, ball_ready_to_drop
    size_index = random.randrange(0, min(6, len(ball_sizes)))
    ball_shape = create_static_ball(space, (ball_position_x, ball_position_y), size_index)
    ball_ready_to_drop = False

ball_timer = 0
ball_timer_threshold = 60
box_left = (width - box_width) / 2
box_right = box_left + box_width

create_new_ball()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN and ball_shape is not None and not ball_ready_to_drop:
                make_ball_dynamic(ball_shape)
                ball_ready_to_drop = True

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        ball_position_x = max(box_left + radius, ball_position_x - 5)
    if keys[pygame.K_RIGHT]:
        ball_position_x = min(box_right - radius, ball_position_x + 5)

    for shape in space.shapes:
        if isinstance(shape, pymunk.Circle) and shape.body.position.y - shape.radius > height:
            game_over = True
            break
    
    if game_over:
        print("Game Over!")
        break

    if ball_shape is not None and not ball_ready_to_drop:
        ball_shape.body.position = pymunk.Vec2d(ball_position_x, ball_position_y)

    if ball_ready_to_drop and ball_shape is not None:
        if ball_shape.body.body_type == pymunk.Body.DYNAMIC:
            ball_timer += 1
            if ball_timer > ball_timer_threshold:
                ball_shape = None
                ball_ready_to_drop = False
                ball_timer = 0
                create_new_ball()

    if not ball_ready_to_drop and ball_shape is None:
        create_new_ball()

    space.step(1 / 50.0)

    screen.fill(WHITE)
    draw_box(screen, (width - box_width) / 2, (height - box_height) / 2, box_width, box_height)

    for shape in space.shapes:
        if isinstance(shape, pymunk.Circle):
            pos = int(shape.body.position.x), int(shape.body.position.y)
            pygame.draw.circle(screen, shape.color, pos, int(shape.radius))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
