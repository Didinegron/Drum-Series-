"""Cut clips from the user's drum video, track camera motion against a clean reference
frame (ORB features + RANSAC similarity transform) and blur the drum-pad logos."""
import sys, os, subprocess, json
import numpy as np, cv2

SRC = '/root/.claude/uploads/181f8862-8b46-53a1-808e-9ac6a1f21b55/d47337df-drum_video.mp4'
OUT = '/tmp/claude-0/-home-user-Tinder-Nope-TinDOG/181f8862-8b46-53a1-808e-9ac6a1f21b55/scratchpad/vid/clips'
REF_T = 33.4
W, H = 1280, 720
# logo ellipses on the reference frame: (cx, cy, rx, ry)
LOGOS = [(535, 370, 85, 62),    # main pad V-Drums + patent text
         (790, 435, 42, 70),    # main pad "Roland" (vertical)
         (232, 237, 55, 30),    # left pad Roland
         (350, 343, 62, 38),    # left pad V-Drums
         (312, 80, 70, 35),     # top-left pad V-Drums
         (636, 75, 70, 35)]     # top-right pad V-Drums

CLIPS = {  # name: (start, end) in the source video, seconds
    'vgrip': (3.0, 14.5),      # both hands, sticks in a V over the pad, tapping
    'sticks': (24.0, 29.5),    # pair of sticks laid across both palms
    'fulcrum': (64.0, 76.5),   # stick resting across one finger, sliding to balance
    'pinch': (77.0, 84.5),     # thumb + first finger pinch
    'pivot': (86.0, 100.0),    # pinched stick rocking freely (wiggle / seesaw)
    'curl': (106.0, 118.0),    # other fingers curled loosely around the stick
    'tap1': (126.0, 136.5),    # one hand tapping, relaxed
    'altern': (140.0, 152.0),  # both hands alternating taps
    'bounce': (188.0, 200.0),  # one hand, stick rebounding off the pad
}

def frames(t0, t1):
    n = int(round((t1 - t0) * 30))
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', str(t0), '-i', SRC, '-frames:v', str(n),
                          '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
    while True:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        yield np.frombuffer(b, np.uint8).reshape(H, W, 3)
    p.wait()

def ref_frame():
    return next(frames(REF_T, REF_T + 0.1))

orb = cv2.ORB_create(3000)
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
REF = ref_frame(); RG = cv2.cvtColor(REF, cv2.COLOR_BGR2GRAY)
# only use background (upper part + sides) for features, hands are mostly lower/centre
kr, dr = orb.detectAndCompute(RG, None)

def transform(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    k, d = orb.detectAndCompute(g, None)
    if d is None or len(k) < 20: return None
    m = sorted(bf.match(dr, d), key=lambda x: x.distance)[:600]
    if len(m) < 20: return None
    src = np.float32([kr[x.queryIdx].pt for x in m]); dst = np.float32([k[x.trainIdx].pt for x in m])
    M, inl = cv2.estimateAffinePartial2D(src, dst, method=cv2.RANSAC, ransacReprojThreshold=4.0, maxIters=3000)
    if M is None or inl.sum() < 25: return None
    return M

def blur_logos(img, M):
    mask = np.zeros((H, W), np.float32)
    s = np.sqrt(M[0, 0] ** 2 + M[1, 0] ** 2); ang = np.degrees(np.arctan2(M[1, 0], M[0, 0]))
    for (cx, cy, rx, ry) in LOGOS:
        x, y = M @ np.array([cx, cy, 1.0])
        cv2.ellipse(mask, (int(x), int(y)), (int(rx * s + 14), int(ry * s + 14)), ang, 0, 360, 1.0, -1)
    mask = cv2.GaussianBlur(mask, (0, 0), 9)[..., None]
    bl = cv2.GaussianBlur(img, (0, 0), 13)
    return (img * (1 - mask) + bl * mask).astype(np.uint8)

def process(name, t0, t1):
    od = os.path.join(OUT, name); os.makedirs(od, exist_ok=True)
    Ms = []; imgs = []
    for f in frames(t0, t1):
        imgs.append(f); Ms.append(transform(f))
    # fill failures + smooth over time
    good = [i for i, M in enumerate(Ms) if M is not None]
    if not good: raise RuntimeError('tracking failed for ' + name)
    for i in range(len(Ms)):
        if Ms[i] is None:
            j = min(good, key=lambda g: abs(g - i)); Ms[i] = Ms[j]
    A = np.array(Ms)
    k = 5
    As = np.array([A[max(0, i - k):i + k + 1].mean(0) for i in range(len(A))])
    for i, (img, M) in enumerate(zip(imgs, As)):
        cv2.imwrite(os.path.join(od, f'{i:04d}.jpg'), blur_logos(img, M), [cv2.IMWRITE_JPEG_QUALITY, 92])
    fails = len(Ms) - len(good)
    return len(imgs), fails

if __name__ == '__main__':
    names = sys.argv[1:] or list(CLIPS)
    info = {}
    for n in names:
        cnt, fails = process(n, *CLIPS[n])
        info[n] = cnt; print(f'{n}: {cnt} frames, tracking gaps filled: {fails}', flush=True)
    meta = os.path.join(OUT, 'meta.json')
    old = json.load(open(meta)) if os.path.exists(meta) else {}
    old.update(info); json.dump(old, open(meta, 'w'))
