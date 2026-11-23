// 영상 컷(Higgsfield 30초 생성본을 컷별로 자른 프레임 시퀀스)을
// renderAt(t)에서 프레임 단위로 정확히 그리기 위한 헬퍼. (headless 렌더에서 <video> 탐색은 프레임이 어긋나서 시퀀스 사용)
//
// 사용:
//   <script src="../clips/clip.js"></script>
//   await Clip.init('assets/clips/', '../clips/clips.json');
//   const img = await Clip.frame('14_S05_C01b_ski_stop_snow', lt);            // 원본 프레임
//   const cut = await Clip.frame('14_S05_C01b_ski_stop_snow', lt, { cut: true }); // 누끼(투명 PNG, 없는 컷은 null)
//   옵션: { speed: 1, offset: 0, loop: false }  — lt(초) * 24fps * speed + offset 프레임, 범위 밖은 첫/끝 프레임 유지
// 반환된 Image는 기존 place()/draw()에 IMG.xxx 대신 그대로 넣으면 된다 (1280x720).
(function () {
  const FPS = 24;
  const cache = new Map();       // src -> Promise<Image>
  const MAX = 240;               // 최근 사용 프레임만 유지 (메모리 제한)
  let BASE = 'assets/clips/';
  let INFO = {};

  function loadImg(src) {
    if (cache.has(src)) { const v = cache.get(src); cache.delete(src); cache.set(src, v); return v; }
    const pr = new Promise((res, rej) => {
      const i = new Image();
      i.onload = () => res(i);
      i.onerror = () => rej(new Error('clip frame ' + src));
      i.src = src;
    });
    cache.set(src, pr);
    if (cache.size > MAX) cache.delete(cache.keys().next().value);
    return pr;
  }

  function index(id, lt, o) {
    const n = INFO[id].frames;
    let k = Math.floor(lt * FPS * (o.speed ?? 1) + 1e-6) + (o.offset ?? 0);
    if (o.loop) k = ((k % n) + n) % n; else k = Math.max(0, Math.min(n - 1, k));
    return k + 1;                // 파일은 f0001부터
  }

  window.Clip = {
    FPS,
    async init(base, manifestUrl) {
      if (base) BASE = base;
      const m = await (await fetch(manifestUrl)).json();
      INFO = Object.fromEntries(m.clips.map(c => [c.id, c]));
      return m;
    },
    info: id => INFO[id],
    duration: id => INFO[id].frames / FPS,
    async frame(id, lt, o = {}) {
      const c = INFO[id];
      if (!c) throw new Error('unknown clip ' + id);
      if (o.cut && !c.cut) return null;
      const k = String(index(id, lt, o)).padStart(4, '0');
      return loadImg(BASE + id + (o.cut ? '_cut/f' + k + '.png' : '/f' + k + '.jpg'));
    },
    // 렌더 전에 특정 구간 프레임을 미리 불러두기 (선택)
    async preload(id, from = 0, to = Infinity, o = {}) {
      const c = INFO[id]; const end = Math.min(to, c.frames / FPS);
      const jobs = [];
      for (let t = from; t < end; t += 1 / FPS) jobs.push(this.frame(id, t, o));
      return Promise.all(jobs);
    },
  };
})();
