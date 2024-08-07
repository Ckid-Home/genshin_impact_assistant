import os.path

from source.interaction.interaction_core import itt
from source.funclib import small_map
from source.util import *
from source.funclib import generic_lib
from source.map.map import genshin_map
from source.manager import asset
from source.common.timer_module import *
from source.assets.movement import *
from source.funclib.cvars import *

itt = itt


# >0:right; <0:left
def move(direction, distance: float = -1, mode=MOVE_START):
    if IS_DEVICE_PC:
        d2k = {
            MOVE_AHEAD: 'w',
            MOVE_BACK: 's',
            MOVE_LEFT: 'a',
            MOVE_RIGHT: 'd'
        }
        if distance == -1:
            if mode == MOVE_START:
                itt.key_down(d2k[direction])
            else:
                itt.key_up(d2k[direction])
        else:
            itt.key_down(d2k[direction])
            itt.delay(0.1 * distance)
            itt.key_up(d2k[direction])
    else:
        pass


jump_timer1 = Timer()
jump_timer2 = Timer()


def jump_timer_reset():
    jump_timer1.reset()


def jump_in_loop(jump_dt: float = 2):
    if jump_timer1.get_diff_time() >= jump_dt:
        jump_timer1.reset()
        jump_timer2.reset()
        itt.key_press('spacebar')
    if jump_timer2.get_diff_time() >= 0.3 and jump_timer2.get_diff_time() <= 2:  # double jump
        itt.key_press('spacebar')
        jump_timer2.start_time -= 2


class JumpInLoop():
    def __init__(self, jump_dt: float = 2) -> None:
        self.jump_dt = jump_dt
        self.jump_timer1 = Timer()
        self.jump_timer2 = Timer()
        self.jump_times = 0
        self.jump_timer3 = Timer()

    def jump_in_loop(self, skip_first=True, jump_dt=None):
        if jump_dt != None:
            self.jump_dt = jump_dt
        if skip_first:
            if self.jump_timer3.get_diff_time() >= 2:  # first
                self.jump_times += 1
                self.jump_timer3.reset()
                return
            elif self.jump_times >= 2:  # 2 first
                self.jump_times = 0
                self.jump_timer3.reset()
            else:
                self.jump_times = 0
                self.jump_timer3.reset()
        if self.jump_timer1.get_diff_time() >= self.jump_dt:
            self.jump_timer1.reset()
            self.jump_timer2.reset()
            itt.key_press('spacebar')
        if self.jump_timer2.get_diff_time() >= 0.3 and self.jump_timer2.get_diff_time() <= 2:  # double jump
            itt.key_press('spacebar')
            self.jump_timer2.start_time -= 2


def angle2movex(angle):
    cvn = maxmin(angle * 10, 500, -500)  # 10: magic num, test from test246.py
    return cvn

def angle2movex_v2(angle):
    cvn = angle * 12  # 10: magic num, test from test246.py
    return cvn

def cview(angle=10, mode=HORIZONTAL, rate=0.9):  # left<0,right>0
    # logger.debug(f"cview: angle: {angle} mode: {mode}")
    if IS_DEVICE_PC:
        cvn = angle2movex(angle) * rate
        if abs(cvn) < 1:
            if cvn < 0:
                cvn = -1
            else:
                cvn = 1
        if mode == HORIZONTAL:
            itt.move_to(int(cvn), 0, relative=True)
        else:
            itt.move_to(0, int(angle), relative=True)

def direct_cview(angel=10):
    itt.move_to(int(angel), 0, relative=True)

def move_view_p(x, y):
    # x,y=point
    itt.move_to(x, y)


def reset_view():
    if IS_DEVICE_PC:
        itt.middle_click()
        itt.delay(0.4)


def calculate_delta_angle(cangle, tangle):
    dangle = cangle - tangle
    if dangle > 180:
        dangle = -(360 - dangle)
    elif dangle < -180:
        dangle = (360 + dangle)
    return dangle


from sklearn.ensemble import IsolationForest

@timer
def discard_abnormal_data(data: list):
    if len(data) >= 3:
        predictions = IsolationForest().fit(np.array(data).reshape(-1, 1)).predict(np.array(data).reshape(-1, 1))
        r = list(np.array(data)[predictions == 1].reshape(1, -1)[0])
        for i in range(len(r)):
            r[i] = int(r[i])
    else:
        r = data
    return r



class CViewDynamicCalibration:
    def __pre_isolation_forest(self, x):
        if x not in self.preprocessed_id:
            possible_angles = self.angles[x]
            pb = discard_abnormal_data(possible_angles)
            self.preprocessed_angles[x] = list(pb).copy()
            self.preprocessed_id.append(x)
        save_json(self.preprocessed_angles, all_path=self.CVDC_PREPROCESSED_CACHE)
        return self.preprocessed_angles[x]

    def run_isolation_forest(self):
        self.__load_CVDC_CACHE()
        logger.info(t2t("Please waiting, CViewDynamicCalibration is loading."))
        for x in self.available_angles:
            x = str(x)
            self.preprocessed_angles[x] = [].copy()
            possible_angles = self.angles[x]
            pb = discard_abnormal_data(possible_angles)
            self.preprocessed_angles[x] = list(pb).copy()
            if x not in self.preprocessed_id:
                self.preprocessed_id.append(x)
            logger.debug(f"run_isolation_forest {x}")
        save_json(self.preprocessed_angles, all_path=self.CVDC_PREPROCESSED_CACHE)
        logger.info(t2t("CViewDynamicCalibration is loaded."))

    def __load_CVDC_CACHE(self):
        if os.path.exists(self.CVDC_CACHE):
            self.angles = load_json(all_path=self.CVDC_CACHE)
            for i in self.available_angles:
                if str(i) not in self.angles.keys():
                    self.angles[str(i)] = []
            # self.available_angles = list(range(0, 175, 1)) TODO:more opt
        else:
            for i in self.available_angles:
                self.angles[str(i)] = []

    def clean_CACHE(self):
        if os.path.exists(self.CVDC_CACHE):
            os.remove(self.CVDC_CACHE)
        if os.path.exists(self.CVDC_PREPROCESSED_CACHE):
            os.remove(self.CVDC_PREPROCESSED_CACHE)

    def __init__(self):
        self.available_angles = list(range(0, 10, 1)) + list(range(10, 180, 5))
        self.CVDC_CACHE = f'{CACHE_PATH}\\cvdc_2.json'
        self.CVDC_PREPROCESSED_CACHE = f'{CACHE_PATH}\\cvdc_preprocessed_2.json'
        self.append_times = 0

        self.preprocessed_id = []
        self.preprocessed_angles = {}
        self.angles = {}
        self.__load_CVDC_CACHE()
        if os.path.exists(self.CVDC_PREPROCESSED_CACHE):
            self.preprocessed_angles = load_json(all_path=self.CVDC_PREPROCESSED_CACHE)
            for i in self.preprocessed_angles.keys():
                if len(self.preprocessed_angles[i]) >= 5:
                    self.preprocessed_id.append(i)

    def calibration_cvdc(self):
        genshin_map.reinit_smallmap()
        self.clean_CACHE()
        self.__init__()
        for ts in range(10):
            for i in range(0, 2000, 50):
                direct_cview(i)
                time.sleep(0.2)
                change_view_to_angle(90, offset=1.5, maxloop= 100)
                logger.info(f't: {ts} i: {i}')
            print(CVDC.angles)
        self.run_isolation_forest()

    def _closest_angle(self, x):
        return str(self.available_angles[np.argmin(abs(np.array(self.available_angles) - x))])

    # @timer
    def append_angle_result(self, move_px, diff_angle):
        if not (10 < abs(diff_angle) < 175):
            return
        logger.trace(f"Append: {move_px} {diff_angle}")
        self.angles[self._closest_angle(abs(diff_angle))].append(abs(move_px))
        self.append_times += 1
        if self.append_times%10==0:
            save_json(self.angles, all_path=self.CVDC_CACHE)

    # @timer
    def predict_target(self, target_angel):
        sign = 1

        if target_angel < 0:
            sign = -1
        target_angel = abs(target_angel)
        if not (10 < target_angel < 175):
            return angle2movex(target_angel) * sign
        # possible_angles = self.angles[]
        # pb = discard_abnormal_data(possible_angles)
        pb = self.__pre_isolation_forest(self._closest_angle(target_angel))
        if len(pb) >= 10:
            logger.trace(f"gpr: {target_angel * sign} -> {np.mean(pb) * sign}")
            return np.mean(pb) * sign
        else:
            return angle2movex_v2(target_angel) * sign


CVDC = CViewDynamicCalibration()


def change_view_to_angle(tangle, stop_func=lambda: False, maxloop=25, offset=5, print_log=True, loop_sleep=0, precise_mode = True):
    i = 0
    dangle = 0
    loop_sleep = 0

    @timer
    def get_rotation():
        last_angle = genshin_map.get_rotation()
        for ii in range(10):  # 过滤不准确的角度
            cangle = genshin_map.get_rotation()
            if diff_angle(cangle, last_angle) < 5 + i * 0.1:
                break
            last_angle = cangle
            if not precise_mode:
                break
        return cangle

    while 1:
        cangle = get_rotation()
        last_angle = cangle
        # print(ii)
        dangle = calculate_delta_angle(cangle, tangle)
        # 感觉有问题，先禁用
        if abs(dangle) < offset:
            break
        move_px = CVDC.predict_target(dangle)  # 根据历史角度移动记录自适应角度移动大小。理论上这个模块应该加载到cview函数里，但是cview不能调用genshin_map，所以先这样吧。
        move_px = round(move_px, 2)
        
        # rate = min((0.6 / 50) * abs(dangle) + 0.4, 1)
        if loop_sleep > 0:
            time.sleep(loop_sleep)
        # print(cangle, dangle, rate)
        # rate = 1
        direct_cview(move_px)
        if i > maxloop:
            break
        if stop_func():
            break
        i += 1
        logger.trace(f"cangle {cangle} dangle {dangle}") #  rate {rate}
        changed_angle = get_rotation()
        if precise_mode:
            CVDC.append_angle_result(move_px, calculate_delta_angle(last_angle, changed_angle))


def view_to_angle_domain(angle, stop_func, deltanum=0.65, maxloop=100, corrected_num=CORRECT_DEGREE):
    if IS_DEVICE_PC:
        cap = itt.capture(posi=small_map.posi_map, jpgmode=FOUR_CHANNELS)
        degree = small_map.jwa_3(cap)
        i = 0
        if not abs(degree - (angle - corrected_num)) < deltanum:
            logger.debug(f"view_to_angle_domain: angle: {angle} deltanum: {deltanum} maxloop: {maxloop} ")
        while not abs(degree - (angle - corrected_num)) < deltanum:
            degree = small_map.jwa_3(itt.capture(posi=small_map.posi_map, jpgmode=FOUR_CHANNELS))
            # print(degree)
            cview((degree - (angle - corrected_num)))
            time.sleep(0.05)
            if i > maxloop:
                break
            if stop_func():
                break
            i += 1
        if i > 1:
            logger.debug('last degree: ' + str(degree))


def view_to_imgicon(cap: np.ndarray, imgicon: asset.ImgIcon):
    corr_rate = 1
    ret_points = match_multiple_img(cap, imgicon.image)
    if len(ret_points) == 0: return False
    points_length = []
    for point in ret_points:
        mx, my = SCREEN_CENTER_X, SCREEN_CENTER_Y
        points_length.append((point[0] - mx) ** 2 + (point[1] - my) ** 2)
    closest_point = ret_points[points_length.index(min(points_length))]  # 获得距离鼠标坐标最近的一个坐标
    px, py = closest_point
    mx, my = SCREEN_CENTER_X, SCREEN_CENTER_Y
    px = (px - mx) / (2.4 * corr_rate)
    py = (py - my) / (2 * corr_rate) + 35  # 获得鼠标坐标偏移量
    # print(px,py)
    px = maxmin(px, 350, -350)
    py = maxmin(py, 350, -350)
    itt.move_to(px, py, relative=True)
    return int(math.sqrt(px ** 2 + py ** 2))  # threshold: 50


# def view_to_angle_teyvat(angle, stop_func, deltanum=1, maxloop=30, corrected_num=CORRECT_DEGREE):
#     if IS_DEVICE_PC:
#         '''加一个场景检测'''
#         i = 0

#         if not abs(degree - (angle - corrected_num)) < deltanum:
#             logger.debug(f"view_to_angle_teyvat: angle: {angle} deltanum: {deltanum} maxloop: {maxloop}")
#         while 1:
#             degree = tracker.get_rotation()
#             change_view_to_angle(degree)
#             time.sleep(0.05)
#             if i > maxloop:
#                 break
#             if abs(degree - (angle - corrected_num)) < deltanum:
#                 break
#             if stop_func():
#                 break
#             i += 1
#         if i > 1:
#             logger.debug('last degree: ' + str(degree))

def calculate_posi2degree(pl, curr_posi = None):
    if curr_posi is None:
        curr_posi = genshin_map.get_position()
    degree = generic_lib.points_angle(curr_posi, pl, coordinate=generic_lib.NEGATIVE_Y)
    if abs(degree) < 1:
        return 0
    if math.isnan(degree):
        print({"NAN"})
        degree = 0
    return degree


def change_view_to_posi(pl, stop_func, max_loop=25, offset=5, print_log=True, curr_posi = None):
    if IS_DEVICE_PC:
        degree = calculate_posi2degree(pl, curr_posi=curr_posi)
        if print_log:
            if abs(degree) >= 2:
                logger.debug(f"change_view_to_posi: pl: {pl}")
        change_view_to_angle(degree, maxloop=max_loop, stop_func=stop_func, offset=offset, print_log=print_log)


def move_to_position(posi, offset=5, stop_func=lambda: False, delay=0.1):
    itt.key_down('w')
    while 1:
        time.sleep(delay)
        curr_posi = genshin_map.get_position()
        if abs(euclidean_distance(curr_posi, posi)) <= offset:
            break

        # print(abs(euclidean_distance(curr_posi, posi)))
        change_view_to_posi(posi, stop_func)
    itt.key_up('w')


def reset_const_val():
    pass


def f():
    return False


def get_current_motion_state() -> str:
    def preprocessing(img):
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        lower_white = np.array([0, 0, 200])
        upper_white = np.array([180, 60, 255])
        mask = cv2.inRange(hsv, lower_white, upper_white)
        return mask

    cap = itt.capture(jpgmode=FOUR_CHANNELS)
    cap = preprocessing(cap)
    img1 = crop(cap.copy(), IconMovementClimb.cap_posi)
    r1 = similar_img(img1, IconMovementClimbing.image[:, :, 0])
    img1 = crop(cap.copy(), IconMovementSwim.cap_posi)
    r2 = similar_img(img1, IconMovementSwimming.image[:, :, 0])
    # cv2.imshow('flying', img1)
    # cv2.waitKey(1)
    img1 = crop(cap.copy(), IconMovementFly.cap_posi)
    r3 = similar_img(img1, IconMovementFlying.image[:, :, 0])
    if max(r1, r2, r3) > 0.8:
        logger.trace(f"get_current_motion_state: climb{round(r1, 2)} swim{round(r2, 2)} fly{round(r3, 2)}")
    if r1 > 0.85:
        return CLIMBING
    if r2 > 0.75:
        return SWIMMING
    if r3 > 0.6:
        return FLYING
    return WALKING
    # if itt.get_img_existence(asset.IconGeneralMotionClimbing):
    #     return CLIMBING
    # elif itt.get_img_existence(asset.IconGeneralMotionFlying):
    #     return FLYING
    # elif itt.get_img_existence(asset.IconGeneralMotionSwimming):
    #     return SWIMMING
    # else:
    #     return WALKING


def move_to_posi_LoopMode(target_posi, stop_func, threshold:float=6):
    """移动到指定坐标。适合用于while循环的模式。

    Args:
        target_posi (_type_): 目标坐标
        stop_func (_type_): 停止函数
    """
    delta_degree = abs(calculate_delta_angle(genshin_map.get_rotation(), calculate_posi2degree(target_posi)))
    if delta_degree >= 20:
        itt.key_up('w')
        change_view_to_posi(target_posi, stop_func=stop_func)
        itt.key_down('w')
    else:
        change_view_to_posi(target_posi, stop_func=stop_func, max_loop=4, offset=2, print_log=False)
    return euclidean_distance(genshin_map.get_position(), target_posi) <= threshold
# if os.path.exists(CVDC.CVDC_PREPROCESSED_CACHE):
#     if time.time() - os.path.getmtime(CVDC.CVDC_PREPROCESSED_CACHE) > 86400:
#         CVDC.run_isolation_forest()

# view_to_angle(-90)
if __name__ == '__main__':
    # print(calibration_angle_shift(times=10))
    # CVDC.run_isolation_forest()
    CVDC.calibration_cvdc()
    # genshin_map.reinit_smallmap()
    # for ts in range(5):
    #     for i in range(0,1500,50):
    #         direct_cview(i)
    #         time.sleep(0.2)
    #         change_view_to_angle(90)
    #         logger.trace(f't: {ts} i: {i}')
    #     print(CVDC.angles)
    #
    # while 1:
    #     time.sleep(0.2)
    #     change_view_to_angle(90)
        # print(genshin_map.get_rotation())
    #     cap = itt.capture(jpgmode=NORMAL_CHANNELS)
    #     ban_posi=asset.IconCommissionCommissionIcon.cap_posi
    #     cap[ban_posi[1]:ban_posi[3],ban_posi[0]:ban_posi[2]]=0
    #     print(view_to_imgicon(cap, asset.IconCommissionInCommission))
    # # cview(-90, VERTICALLY)
    # move_to_position([71, -2205])
