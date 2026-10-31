export const meta = {
  name: 'plan-step-tdd',
  description: 'Làm lần lượt các bước của một kế hoạch đã duyệt, mỗi bước một agent: test trước, cài nhỏ nhất, toàn bộ pytest, cổng đo, một commit local. Rồi soát hai góc nhìn có bác bỏ (workflow review-lenses) và sửa phát hiện đã xác nhận, test hỏng trước.',
  whenToUse: 'Khi kế hoạch đã duyệt có nhiều bước nối nhau và mỗi bước có đặc tả riêng (danh sách "Test trước", cổng đo). Tham số và ví dụ: docs/quy-trinh.md, mục "Workflow có sẵn".',
  phases: [
    { title: 'Làm', detail: 'tuần tự, mỗi bước một agent, một commit local' },
    { title: 'Soát', detail: 'hai góc nhìn, mỗi phát hiện bị bác bỏ thử (workflow review-lenses)' },
    { title: 'Sửa', detail: 'test hỏng trước, một commit local' },
  ],
}

// Tham số (args): plan, steps (bắt buộc), trailer (bắt buộc), lenses, context, gates, store, recordInPlan, fixNice,
// python, pytest, scratch, reviewScriptPath. Ý nghĩa từng tham số: docs/quy-trinh.md.
const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const need = (ok, msg) => { if (!ok) throw new Error('plan-step-tdd: ' + msg) }

const MAX_AGENTS = 10 // bước + 2 mỗi góc soát + 1 sửa; quá thì chia làm hai lần chạy
need(A.plan, 'cần args.plan: đường dẫn tệp kế hoạch, vd "docs/ke-hoach/ke-hoach-p1.md"')
need(Array.isArray(A.steps) && A.steps.length, 'cần args.steps: mảng chuỗi (tên mục) hoặc {key, section, task?}')
need(A.trailer, 'cần args.trailer: hai dòng Co-Authored-By và Claude-Session chép NGUYÊN VĂN từ lời nhắc ghi công của phiên điều phối (agent con không thấy lời nhắc đó)')
const steps = A.steps.map(s => typeof s === 'string' ? { key: s, section: s } : { key: s.key, section: s.section || s.key, task: s.task || '' })
need(steps.every(s => s.key && s.section), 'mỗi bước cần key và section')
need(new Set(steps.map(s => s.key)).size === steps.length, 'key bước bị trùng')

const py = A.python || 'python'
const pytest = A.pytest || `${py} -m pytest -q`
const sp = A.scratch || 'thư mục scratchpad của phiên'
const recordInPlan = A.recordInPlan !== false
const reviewLenses = A.lenses && A.lenses.length ? A.lenses : ['bugs', 'tests']
need(reviewLenses.length <= 3, 'tối đa 3 góc nhìn soát')
need(steps.length + reviewLenses.length * 2 + 1 <= MAX_AGENTS, `${steps.length} bước và ${reviewLenses.length} góc soát cần ${steps.length + reviewLenses.length * 2 + 1} agent, quá ${MAX_AGENTS}; chia làm hai lần chạy`)

const COMMON = `${A.context || 'Repo hiện tại là Soi Luật: app tra cứu văn bản pháp luật Việt Nam chạy offline cho một người dùng trên 127.0.0.1 (FastAPI, Jinja, JS thuần, SQLite FTS5). Bản đồ module: docs/kien-truc.md.'}
ĐẶC TẢ CÓ THẨM QUYỀN của mỗi bước là mục tương ứng trong ${A.plan} (đọc hết mục: rủi ro, danh sách "Test trước", cổng đo, trạng thái). Python: \`${py}\`; test: \`${pytest}\`. Tiếng Việt cho test, comment, thông điệp commit. Không pkill -f; máy chủ nào bạn bật thì ghi PID vào tệp và kill theo PID đó. Kiểm trên trình duyệt bằng Playwright cho Node (NODE_PATH=$(npm root -g))${A.store ? ` với máy chủ chạy bằng SOILUAT_DATA=${A.store} (kho thử, không phải kho thật)` : ' trên một kho thử'}, cổng rảnh. Script thử và ảnh để trong ${sp}.
Các agent khác có thể đang sửa cùng cây: chỉ đụng tệp cần cho bước của bạn, \`git add\` đúng các tệp đó (không \`git add -A\`, không \`git stash\`), gặp index.lock thì đợi vài giây rồi thử lại.`

const COMMIT_RULES = `Đúng MỘT commit local (KHÔNG push). Thông điệp tiếng Việt: đã đổi gì, kiểm bằng gì (tên test, lệnh, số đo kèm bộ dữ liệu, tập chia, n). Trailer chép NGUYÊN VĂN hai dòng sau và kết thúc thông điệp bằng chúng:
${A.trailer}
Quy trình: ghi thông điệp ra tệp trong ${sp}, chạy \`grep -E '^(Co-Authored-By|Claude-Session):' <tệp>\` và so với hai dòng trên, rồi \`git commit -F <tệp>\`; sau commit chạy \`git log -1 --format=%B\` và so lại. Sai thì \`git commit --amend\` sửa dòng đó.`

const BUILT = { type: 'object', properties: {
  step: { type: 'string' }, status: { type: 'string', enum: ['done', 'blocked'] }, commit: { type: 'string' },
  tests: { type: 'array', items: { type: 'object', properties: { name: { type: 'string' }, checks: { type: 'string' } }, required: ['name', 'checks'] } },
  measurements: { type: 'string', description: 'số đo kèm bộ dữ liệu, tập chia, n, mã' },
  not_done: { type: 'string', description: 'phần đặc tả chưa làm và vì sao; hoặc lý do bị chặn' } },
  required: ['step', 'status', 'commit', 'tests', 'measurements', 'not_done'] }
const FIXED = { type: 'object', properties: { items: { type: 'array', items: { type: 'object', properties: {
  id: { type: 'string' }, outcome: { type: 'string', enum: ['fixed', 'refuted', 'deferred'] }, test: { type: 'string' }, note: { type: 'string' } },
  required: ['id', 'outcome', 'note'] } }, commit: { type: 'string' } }, required: ['items', 'commit'] }

log(`plan-step-tdd: ${steps.length} bước (${steps.map(s => s.key).join(' > ')}), soát ${reviewLenses.length} góc nhìn: khoảng ${steps.length + reviewLenses.length * 2 + 1} agent`)

phase('Làm')
const built = []
for (const s of steps) {
  const r = await agent(`${COMMON}

BƯỚC ${s.key}: mục "${s.section}" trong ${A.plan}. ${s.task}
Làm theo thứ tự:
1. Đọc hết mục của bước trong kế hoạch. Đọc commit của các bước trước trong lượt chạy này (\`git log -8 --format='%h %s'\`, \`git show --stat\`) để làm tiếp trên chúng, không làm lại.
2. TEST TRƯỚC: viết từng test mà mục liệt kê; chạy, thấy nó HỎNG trên mã hiện tại (test không thể hỏng thì nói rõ vì sao). Chưa thấy hỏng thì chưa sửa mã.
3. Cài đặt thay đổi nhỏ nhất đủ việc: không thêm tầng ngoài những gì mục nêu tên; tìm hàm có sẵn dùng lại trước khi viết mới; grep mọi nơi gọi của hàm bạn đổi.
4. Chạy TOÀN BỘ \`${pytest}\`, phải xanh.
5. Cổng đo: nếu bước chạm tìm kiếm, parser, trình đọc hay giao diện, chạy đúng cổng trong docs/quy-trinh.md mục "Cổng đo" và ghi số kèm bộ dữ liệu, tập chia, n, mã. Cổng trượt thì dừng và nói rõ (status=blocked), không vá số. ${A.gates || ''}
6. Trước khi commit, đọc lại mục của bước trong kế hoạch (\`git diff -- ${A.plan}\` xem tệp có bị agent khác viết lại không). Mục đổi thì đối chiếu lại việc đã làm.
${recordInPlan ? `7. Ghi trạng thái và số đo của bước vào ${A.plan} trong CÙNG commit, sửa tại chỗ tiêu đề hoặc gạch đầu dòng đầu của mục, KHÔNG thêm dòng (skill plan-doc-line-reference-edits); kiểm \`diff <(git show HEAD:${A.plan} | wc -l) <(wc -l < ${A.plan})\` không in gì.\n8.` : '7.'} ${COMMIT_RULES}
Nếu bị chặn thật (thiếu quyết định của chủ dự án, cổng trượt, đặc tả mâu thuẫn với luật dự án): không commit nửa vời, trả status=blocked, commit="" và nói rõ lý do ở not_done.
Trả: step, status, commit, tests (tên: kiểm gì), measurements, not_done.`,
    { label: `lam:${s.key}`, phase: 'Làm', schema: BUILT })
  built.push({ step: s.key, report: r })
  if (!r || r.status !== 'done' || !r.commit) { log(`${s.key} ${r ? 'bị chặn' : 'mất kết quả'}: dừng chuỗi, không làm bước sau trên nền chưa xong`); break }
  log(`${s.key} xong: ${r.commit}`)
}
const commits = built.filter(b => b.report && b.report.status === 'done' && b.report.commit).map(b => b.report.commit)
if (!commits.length) return { built, review: null, fixed: null, note: 'không có commit nào để soát' }

phase('Soát')
const reviewArgs = { commits, lenses: reviewLenses, context: A.context, python: py, pytest, scratch: A.scratch,
  rejected: 'những việc kế hoạch ghi rõ là không làm hay dời sang phase sau (mục "Không làm", "Dời")', paths: A.paths }
let review
try { review = await workflow('review-lenses', reviewArgs) }
catch (e) { log(`workflow('review-lenses') lỗi (${e && e.message}); thử theo scriptPath`); review = await workflow({ scriptPath: A.reviewScriptPath || '.claude/workflows/review-lenses.js' }, reviewArgs) }
const todo = (review.confirmed || []).filter(f => f.group !== 'nice' || A.fixNice === true)
log(`soát: ${(review.confirmed || []).length} xác nhận, cần sửa ${todo.length}`)

phase('Sửa')
let fixed = null
if (todo.length) {
  fixed = await agent(`${COMMON}

Áp các phát hiện đã qua bác bỏ dưới đây lên HEAD (các commit của lượt này: ${commits.join(', ')}). Với MỖI mục: kiểm lại là có thật ở mã hiện tại; thật thì viết test hồi quy (hoặc kiểm Playwright cho lỗi thuần giao diện) HỎNG trước, chạy thấy hỏng, sửa nhỏ nhất ở mã dùng chung (grep nơi gọi), chạy thấy qua; không thật thì outcome=refuted một dòng lý do, không đổi mã. Mục cần chủ dự án quyết thì outcome=deferred kèm lý do. Chạy TOÀN BỘ \`${pytest}\`, phải xanh. Bản sửa làm đổi số đã ghi trong ${A.plan} thì sửa số đó tại chỗ trong cùng commit, không thêm dòng.
${COMMIT_RULES} Thông điệp liệt kê từng id và cách sửa.
Trả bảng: id, fixed/refuted/deferred, tên test hay lý do; và hash commit.

PHÁT HIỆN:
${JSON.stringify(todo, null, 1)}`, { label: 'sua', phase: 'Sửa', schema: FIXED })
} else log('không có phát hiện cần sửa')

return { built, review, fixed }
