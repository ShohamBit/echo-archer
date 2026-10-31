"""Animated vector creature silhouettes, oriented toward committed attacks."""
import math
import pygame
import pygame.gfxdraw


def draw_creature(surface, enemy, point, scale, clock, flashing=True):
    p, r = point(enemy.pos), enemy.radius * scale
    forward = enemy.heading
    side = forward.rotate(90)
    color = (235, 244, 240) if enemy.flash > 0 and flashing else {
        "chaser": (255, 108, 126), "tank": (238, 186, 108),
        "shooter": (182, 148, 245), "nugget": (251, 219, 115)}[enemy.kind]
    dark = (30, 30, 44)

    def at(x, y):
        return p + side * x * r + forward * y * r

    def plate(vertices, fill):
        coords = [tuple(map(round, at(x, y))) for x, y in vertices]
        pygame.gfxdraw.filled_polygon(surface, coords, fill)
        pygame.gfxdraw.aapolygon(surface, coords, color)

    def line(vertices, ink=color, width=2):
        pygame.draw.lines(surface, ink, False, [at(x, y) for x, y in vertices], width)

    if enemy.phase == "windup":
        reach = 300 if enemy.kind != "shooter" else 650
        for angle in ((-12, 0, 12) if enemy.kind == "shooter" else (0,)):
            pygame.draw.aaline(surface, color, p + forward * r,
                               point(enemy.pos + forward.rotate(angle) * reach))
        pygame.draw.arc(surface, color, (p.x-r*1.2, p.y-r*1.2, r*2.4, r*2.4),
                        clock * 2, clock * 2 + 4.5, 2)
    stride = math.sin(clock * 9 + enemy.id) * .15 if enemy.phase == "hunt" else 0
    if enemy.kind == "chaser":
        # A mantis hunter: paired sickles, segmented abdomen, glowing visor.
        for sign in (-1, 1):
            line([(sign*.32, -.4), (sign*.9, -.7+stride), (sign*1.1, -.2)])
            line([(sign*.36, .1), (sign*.95, .2-stride), (sign*.6, 1.02)], width=3)
            plate([(sign*.92, .15), (sign*.65, 1.02), (sign*.48, .4)], color)
        plate([(-.45, -.45), (0, -.98), (.45, -.45), (.36, .46), (0, .83), (-.36, .46)], dark)
        line([(-.25, .43), (0, .56), (.25, .43)], (255, 220, 202), 3)
        line([(-.24, -.27), (.24, -.27)])
    elif enemy.kind in ("tank", "nugget"):
        # A six-legged plated scarab, broad enough to identify at a glance.
        for sign in (-1, 1):
            for j in (-1, 0, 1):
                line([(sign*.4, j*.43), (sign*.85, j*.6+stride), (sign*1.04, j*.7+.22)], width=3)
        plate([(0, -1), (.7, -.6), (.77, .45), (.3, .88), (0, .62), (-.3, .88), (-.77, .45), (-.7, -.6)], dark)
        plate([(-.58, -.4), (-.12, -.72), (-.08, .51), (-.5, .63)], color)
        plate([(.58, -.4), (.12, -.72), (.08, .51), (.5, .63)], color)
        line([(-.25, .7), (0, 1.05), (.25, .7)], width=3)
    else:
        # A hovering, horned caster with a ragged cloak and suspended eye.
        bob = math.sin(clock * 4 + enemy.id) * .07
        plate([(-.42, .3+bob), (-.85, -.86), (-.3, -.65), (0, -1.03), (.35, -.65),
               (.85, -.86), (.42, .3+bob)], dark)
        for sign in (-1, 1):
            line([(sign*.35, .25+bob), (sign*.8, .85+bob), (sign*.45, .62+bob)], width=3)
        pygame.draw.ellipse(surface, color, (p.x-r*.4, p.y-r*.24, r*.8, r*.48))
        pygame.draw.circle(surface, dark, p, max(2, round(r*.12)))
        for sign in (-1, 1):
            orb = at(sign*.9, .05+math.sin(clock*4)*.18)
            pygame.draw.circle(surface, color, orb, max(2, round(r*.09)))
