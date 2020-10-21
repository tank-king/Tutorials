import turtle

screen = turtle.Screen()

screen.title('Creating Buttons in Python Turtle')
screen.bgcolor('#111111')
screen.tracer(0)

pen = turtle.Turtle()
pen.hideturtle()
pen.pencolor('#111111')
pen.fillcolor('white')

Button_x = -50
Button_y = -50
ButtonLength = 100
ButtonWidth = 50

mode = 'dark'


def draw_rect_button(pen, message = 'Click Me'):
    pen.penup()
    pen.begin_fill()
    pen.goto(Button_x, Button_y)
    pen.goto(Button_x + ButtonLength, Button_y)
    pen.goto(Button_x + ButtonLength, Button_y + ButtonWidth)
    pen.goto(Button_x, Button_y + ButtonWidth)
    pen.goto(Button_x, Button_y)
    pen.end_fill()
    pen.goto(Button_x + 15, Button_y + 15)
    pen.write(message, font = ('Arial', 15, 'normal'))


draw_rect_button(pen)


def button_click(x, y):
    global mode
    if Button_x <= x <= Button_x + ButtonLength:
        if Button_y <= y <= Button_y + ButtonWidth:
            print('Clicked')
            if mode == 'dark':
                screen.bgcolor('orange')
                mode = 'light'
            else:
                screen.bgcolor('#111111')
                mode = 'dark'


def circle_button(pen, x, y, r):
    pen.pencolor('white')
    pen.goto(x, y)
    pen.begin_fill()
    pen.circle(r)
    pen.end_fill()
    pen.pencolor('#111111')
    pen.goto(x - 35, y + 35)
    pen.write('Click me', font = ('Arial', 15, 'normal'))


# circle_button(pen, 0, 0, 50) # uncomment this to draw the circular button


def distance(p1, p2):
    return (p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2


def circle_button_click(x, y):
    global mode
    if distance((0, 50), (x, y)) <= 50 ** 2:
        print('Clicked')
        if mode == 'dark':
            screen.bgcolor('orange')
            mode = 'light'
        else:
            screen.bgcolor('#111111')
            mode = 'dark'


screen.onclick(button_click)  # comment this to stop rectangle button and see circle button
screen.onclick(circle_button_click)  # uncomment this for circle button

turtle.done()
