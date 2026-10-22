## Makes the physics modules (plain Python files in this folder) importable,
## and reloads them with Shift+R. From init -599 on, any file can use them:
##
##     init python:
##         import uxphys_collide
##
## They're .py modules rather than .rpy code so they skip Ren'Py's rollback
## machinery and run under plain python3 for the tests. Physics objects aren't
## saved: rebuild them from plain data in gs after a load.

init -600 python:
    renpy.add_python_directory("code/physics/")

    import uxphys_math
    import uxphys_collide
    import uxphys_path

    config.reload_modules.extend(["uxphys_math", "uxphys_collide", "uxphys_path"])
