import time
import math


class DTAwareValue(object):
    def __init__(self, d_dt=None, start_value=None):
        if start_value is None:
            start_value = 0  # Default is to start at 0
        if d_dt is None:
            d_dt = 1  # Default is one Hz
        self.value = start_value
        self.d_dt = d_dt

    def dt(self, dt):
        self.value += self.d_dt * dt


class DTAwarePeriodicValue(DTAwareValue):
    def __init__(self, d_dt=None, start_value=None, limit=None, reset_func=None):
        super().__init__(d_dt=d_dt, start_value=start_value)
        if limit is None:
            limit = 1  # Default is period of 1
        self.limit = limit
        self.reset_func = reset_func

    def dt(self, dt):
        self.value = self.value + self.d_dt * dt
        if self.value > self.limit:
            self.value = self.value % self.limit
            if self.reset_func is not None:
                self.reset_func()


class DTAwareObjectRotation(DTAwarePeriodicValue):
    def __init__(self, d_dt=None, start_value=None, limit=None, choices=None, initial_choice=None):
        super().__init__(d_dt=d_dt, start_value=start_value, limit=limit, reset_func=self.rotate_object)
        if choices is None:
            choices = []
        if initial_choice is not None and initial_choice not in choices:
            raise ValueError('Initial choice passed to DTAwareObjectRotation must be element of the given choices: {:s} not in {:s}'.format(str(initial_choice), str(choices)))
        self.choices = list(choices)
        self.choice = initial_choice
        self.idx = self.choices.index(self.choice)

    def rotate_object(self):
        if self.choices is None or len(self.choices) == 0:
            pass
        self.idx = (self.idx+1) % len(self.choices)
        self.choice = self.choices[self.idx]

    def get_current_object(self):
        return self.choice


class DTAwareRotation(DTAwarePeriodicValue):
    __twopi = math.pi*2

    def __init__(self, d_dt=None, start_rotation=None, reset_func=None):
        super().__init__(d_dt=d_dt, start_value=start_rotation, limit=self.__twopi, reset_func=reset_func)
        if d_dt is None:
            d_dt = self.__twopi  # Default is one circle a second
        self.d_dt = d_dt

    def get_rotation(self):
        return self.value

    def get_rotation_degrees(self):
        return self.value / self.__twopi * 360


class FPSClock(object):
    def __init__(self, target_fps=None):
        if target_fps is None:
            target_fps = 60
        self.target_fps = target_fps
        self.dt_target = 1/self.target_fps
        self.pre_frame = None
        self.post_render = None
        self.post_frame = None
        self.dt = 0
        self.dt_render = 0

    # Start a new frame
    def start_frame(self):
        if self.post_frame is not None and self.pre_frame is not None:
            self.dt = self.post_frame - self.pre_frame
        self.pre_frame = time.time()

    # Indicate that all work is finished, and we are ready to sleep
    def finish_render(self):
        self.post_render = time.time()
        if self.pre_frame is not None:
            self.dt_render = self.post_render - self.pre_frame

    # Indicate that we have finished with this frame entirely
    def finish_frame(self):
        self.post_frame = time.time()

    def get_dt(self):
        return self.dt

    def get_dt_target(self):
        return self.dt_target

    def get_sleep_time(self):
        return self.dt_target - self.dt_render

    def get_last_render_time(self):
        return self.dt_render
