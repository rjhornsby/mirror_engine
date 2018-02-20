import time
import lib.VL53L0X as VL53L0X
from array import array
import statistics
from logger import Logger
import threading


class DME:
    def __init__(self, threshold, sample_count):
        self.thr = None
        self.stopping = False
        self.tof = VL53L0X.VL53L0X()
        self.distance_threshold = threshold
        self.sample_count = sample_count
        self.distances = array('H')
        self.tof.start_ranging(VL53L0X.VL53L0X_GOOD_ACCURACY_MODE)
        self.ready = False

    def cleanup(self):
        self.tof.stop_ranging()

    def average(self):
        return int(statistics.mean(self.distances))

    def instant(self):
        return self.tof.get_distance()

    def in_range(self):
        if len(self.distances) < self.sample_count:
            Logger.write.info('Not enough samples (' + str(len(self.distances)) + '/' + str(self.sample_count) + ')')
            return False
        else:
            if not self.ready:
                self.ready = True
                Logger.write.info(
                    'Sample threshold reached (' + str(len(self.distances)) + '/' + str(self.sample_count) + ')')
            return self.average() < self.distance_threshold

    def stop(self):
        self.stopping = True

    def run(self):
        if self.thr is not None:
            if self.thr.isAlive():
                return
        self.thr = DMEThread(0, 'loop', self)
        self.stopping = False
        self.thr.start()

    def loop(self):
        while not self.stopping:
            distance = self.instant()
            if len(self.distances) >= self.sample_count:
                self.distances.pop(0)

            self.distances.append(distance)

            time.sleep(0.1)

        self.cleanup()


class DMEThread(threading.Thread):
    def __init__(self, thread_id, name, tof_sensor):
        threading.Thread.__init__(self)
        self.threadID = thread_id
        self.name = name
        self.tof_sensor = tof_sensor

    def run(self):
        self.tof_sensor.loop()
