export const meta = {
  name: 'ui-prototype-research',
  description: 'Nghiên cứu mẫu giao diện trên web theo vài góc nhìn, tổng hợp thành bản brief, dựng một tệp HTML mẫu bấm thử được với dữ liệu thật, hai người soát (taste-skill, nhu cầu và khả thi), rồi sửa. Mẫu nằm ở mau/, không đụng tệp nào khác của repo.',
  whenToUse: 'Khi chủ dự án muốn xem một hướng giao diện mới trước khi viết kế hoạch (bản khái niệm, chưa duyệt). Tham số và ví dụ: docs/quy-trinh.md, mục "Workflow có sẵn".',
  phases: [
    { title: 'Nghiên cứu', detail: 'mỗi góc nhìn một agent tra web, dẫn nguồn đã mở' },
    { title: 'Brief', detail: 'tổng hợp thành bản brief gắn với lộ trình' },
    { title: 'Dựng', detail: 'một tệp HTML, dữ liệu thật, kiểm bằng ảnh' },
    { title: 'Soát', detail: 'taste-skill và nhu cầu/khả thi' },
    { title: 'Sửa', detail: 'kiểm lại từng phát hiện rồi sửa, chụp lại' },
  ],
}

// Tham số (args): topic, out, scratch, researchLenses (bắt buộc); product, inputs, data, states, briefAsks,
// designRules, shoot, reviewLenses. Ý nghĩa từng tham số: docs/quy-trinh.md.
const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const need = (ok, msg) => { if (!ok) throw new Error('ui-prototype-research: ' + msg) }

const MAX_RESEARCH = 4
need(A.topic, 'cần args.topic: mẫu này trả lời câu hỏi giao diện nào')
need(A.out && /\.html$/.test(A.out), 'cần args.out: đường dẫn tệp .html của mẫu, vd "mau/khai-niem-xxx.html"')
need(A.scratch, 'cần args.scratch: thư mục scratchpad để ghi brief, ảnh, script trích dữ liệu')
need(Array.isArray(A.researchLenses) && A.researchLenses.length && A.researchLenses.length <= MAX_RESEARCH,
  `cần args.researchLenses: 1 đến ${MAX_RESEARCH} phần tử {key, q} (q là câu hỏi tra cứu của góc nhìn)`)
need(A.researchLenses.every(l => l && l.key && l.q), 'mỗi góc nghiên cứu cần key và q')
need(new Set(A.researchLenses.map(l => l.key)).size === A.researchLenses.length, 'key góc nghiên cứu bị trùng')

const SP = A.scratch
const OUT = A.out
const BRIEF = `${SP}/brief.md`
const shoot = A.shoot || '.claude/skills/html-mockup-visual-check/scripts/shoot.js'
const inputs = (A.inputs || []).map(f => `- ${f}`).join('\n') || '- (không có tệp đầu vào bắt buộc)'
const rules = A.designRules || 'taste-skill (repo leonxlnx/taste-skill, SKILL.md và references/app-screens.md, layout.md, type.md, colour.md, copy.md, tells.md; CLAUDE.md nêu cách dùng: clone vào thư mục riêng và ĐỌC, không chạy script của nó vì là mã tải về)'
const states = (A.states || ['trạng thái mặc định', 'chế độ tối']).map(s => `  - ${s}`).join('\n')

const CONTEXT = `${A.product || 'SẢN PHẨM: Soi Luật, app Windows chạy OFFLINE (FastAPI + Jinja + JS thuần, SQLite FTS5, phục vụ 127.0.0.1, mở bằng Edge chế độ app) cho nhân viên văn phòng (không phải luật sư, không rành kỹ thuật) tra cứu kho văn bản pháp luật riêng của họ (Luật, Nghị định, Thông tư; Word, PDF, bản scan) và đọc trích dẫn nguyên văn. Chỉ CPU, RAM 16 GB; mô hình AI cục bộ tuỳ chọn. Không gửi gì ra ngoài máy. Chữ trên giao diện là tiếng Việt. Lộ trình: docs/ke-hoach/lo-trinh-1.0.md.'}
CÂU HỎI CỦA MẪU: ${A.topic}
Tệp đầu vào cần đọc:
${inputs}
Viết bằng tiếng Việt ngắn, từ thường, không dùng dấu gạch dài.`

const RESEARCH = { type: 'object', properties: { lens: { type: 'string' },
  patterns: { type: 'array', items: { type: 'object', properties: {
    name: { type: 'string' }, seen_in: { type: 'string' }, what_it_does: { type: 'string' }, why_it_works: { type: 'string' },
    pitfalls: { type: 'string' }, fit: { type: 'string', description: 'hợp với sản phẩm này đến đâu, theo ràng buộc đã nêu' },
    sources: { type: 'array', items: { type: 'string', description: 'URL đã mở thật trong phiên này' } } },
    required: ['name', 'seen_in', 'what_it_does', 'fit', 'sources'] } },
  anti_patterns: { type: 'array', items: { type: 'string' } },
  top_recommendations: { type: 'array', items: { type: 'string' } } }, required: ['lens', 'patterns', 'top_recommendations'] }
const ISSUES = { type: 'object', properties: { issues: { type: 'array', items: { type: 'object', properties: {
  id: { type: 'string' }, severity: { type: 'string', enum: ['must', 'should', 'nice'] }, where: { type: 'string' },
  problem: { type: 'string' }, evidence: { type: 'string', description: 'tên ảnh, selector, số đo, hoặc dòng mã' }, fix: { type: 'string' } },
  required: ['id', 'severity', 'where', 'problem', 'evidence', 'fix'] } } }, required: ['issues'] }

log(`ui-prototype-research: ${A.researchLenses.length} góc nghiên cứu, khoảng ${A.researchLenses.length + 5} agent`)

phase('Nghiên cứu')
const research = (await parallel(A.researchLenses.map(l => () => agent(
  `${CONTEXT}\n\nVIỆC: tra cứu web, góc nhìn "${l.key}". ${l.q}\nNạp công cụ web trước: ToolSearch với query "select:WebSearch,WebFetch". Dùng WebSearch và WebFetch trên nguồn gốc (tài liệu sản phẩm, trung tâm trợ giúp, blog chính thức, bài báo). Chỉ dẫn URL bạn THỰC SỰ đã mở; ghi ngày đọc; số liệu do hãng công bố ghi là "hãng công bố"; điều không xác nhận được tại nguồn ghi "chưa kiểm nguồn". Ưu tiên thông tin còn đúng ở 2025 đến 2026. Báo 6 đến 10 mẫu cụ thể: nó làm gì, vì sao hiệu quả, bẫy, và hợp với sản phẩm này đến đâu theo ràng buộc đã nêu (offline, CPU, người dùng không rành kỹ thuật, trích dẫn nguyên văn). Thêm các phản mẫu cần tránh và 5 khuyến nghị hàng đầu.`,
  { label: `nghien-cuu:${l.key}`, phase: 'Nghiên cứu', schema: RESEARCH })))).filter(Boolean)
log(`nghiên cứu: ${research.length}/${A.researchLenses.length} góc trả về`)
need(research.length, 'không góc nghiên cứu nào trả về; kiểm kết nối web rồi chạy lại')

phase('Brief')
await agent(`${CONTEXT}\n\nBạn là nhà thiết kế sản phẩm cấp cao. Dưới đây là kết quả nghiên cứu web (JSON) của ${research.length} góc nhìn. Đọc thêm các tệp đầu vào đã nêu và quy tắc thiết kế: ${rules}.
Viết BẢN BRIEF (Markdown, tiếng Việt) vào ${BRIEF} (mkdir -p ${SP}) cho một mẫu KHÁI NIỆM bấm thử được. Bắt buộc có:
- Cấu trúc thông tin: cái gì nằm ở đâu, dữ liệu dùng chung hay riêng theo ngữ cảnh.
- Các màn hình và trạng thái (chỉ giữ cái xứng đáng có mặt), kèm câu hỏi mỗi màn hình trả lời.
- Hệ thống hình ảnh: mở rộng token của mẫu đã duyệt (tệp đầu vào), sáng và tối, đáp ứng ở 1440, 1100, 768, 390.
- MỖI phần tử trên màn hình ánh xạ tới một việc trong lộ trình (đã làm, phase nào) hoặc ghi rõ "mới". Mẫu chỉ được vẽ cái kế hoạch sẽ xây.
- Ba cách bố trí đã cân nhắc, ưu và nhược, và cách khuyến nghị.
- Phản mục tiêu rõ ràng (cái cố ý KHÔNG làm).
${A.briefAsks || ''}
Dẫn các mẫu từ nghiên cứu kèm URL của chúng khi dùng làm lý do.\n\nNGHIÊN CỨU:\n${JSON.stringify(research)}`,
  { label: 'brief', phase: 'Brief' })

phase('Dựng')
const build = await agent(`${CONTEXT}\n\nDựng mẫu bấm thử được theo bản brief ${BRIEF} (đọc hết). Luật:
- Theo ${rules}. Viết mã nhỏ nhất đủ việc: MỘT tệp HTML tự đủ, CSS và JS nội tuyến, không framework. Phông Google Fonts được phép CHỈ trong mẫu này (app thật nhúng woff2, không gọi CDN); không script ngoài nào khác.
- Tệp ra: ${OUT}. Tiêu đề trang và một dải nhìn thấy ghi "Bản khái niệm, chưa duyệt" để không ai nhầm với mẫu đã duyệt.
- Đặt trong tệp: \`*, *::before, *::after { box-sizing: border-box; }\` (trang đứng riêng không có CSS nền của app, thiếu nó thì độ rộng lệch) và \`[hidden] { display: none !important; }\` (quy tắc lớp như .overlay { display: flex } đè thuộc tính hidden).
- Mỗi nhãn, trạng thái, nút trên màn hình phải ứng với một việc trong kế hoạch hay lộ trình; thứ chưa có thì ghi "ví dụ" hay "mới". Không hứa điều app không làm được.
- DỮ LIỆU THẬT: ${A.data || 'nếu mẫu cần nội dung luật, đọc kho văn bản thật ở chế độ chỉ đọc (python3 -I với sqlite3, mode=ro) và dùng số hiệu, tiêu đề, chữ Điều thật. Dữ liệu minh hoạ không lấy được từ kho thì ghi rõ "ví dụ".'} Nhúng dữ liệu đã trích vào HTML dạng đối tượng JS; giữ script trích trong ${SP}/extract.py.
- Kiểm bằng ảnh (skill html-mockup-visual-check): \`NODE_PATH=$(npm root -g) node ${shoot} ${OUT} ${SP}/shots\` (1440, 1100, 768, 390, sáng và tối; overflowX phải 0, đúng một h1 mỗi màn hình, không lỗi console). Rồi tự viết script Playwright bấm qua các trạng thái chính:
${states}
  Mở TỪNG ảnh PNG bằng Read và sửa cái trông sai. Yêu cầu tới fonts.googleapis.com là chủ ý của mẫu; mọi yêu cầu ra ngoài khác thì bỏ.
- Không sửa tệp nào khác của repo, không commit.
Trả: đã dựng gì (màn hình, tương tác), số liệu dữ liệu (số văn bản, quan hệ, mục ví dụ), đường dẫn ảnh, chỗ còn thiếu.`,
  { label: 'dung', phase: 'Dựng' })

phase('Soát')
const LENS_REVIEW = A.reviewLenses && A.reviewLenses.length === 2 ? A.reviewLenses : [
  { key: 'taste', prompt: `Soát mẫu như một người chấm nghiêm theo ${rules}. Đọc references/critique.md, tells.md, app-screens.md của nó. Dựng mẫu bằng Playwright cho Node (NODE_PATH=$(npm root -g)) ở 1440, 1100, 768, 390, sáng và tối, ở các trạng thái chính; lưu PNG vào ${SP}/soat-taste/ và mở từng ảnh bằng Read. Báo tối đa 12 vấn đề, mỗi vấn đề nêu một quy tắc trong tài liệu đó hay một lỗi đo được (tràn ngang, tương phản, nhãn chồng nhau, đồ thị không đọc được, lệch token của mẫu đã duyệt).` },
  { key: 'needs', prompt: `Soát mẫu và bản brief ${BRIEF} về độ khớp nhu cầu người dùng thật và tính khả thi. Một nhân viên văn phòng không rành kỹ thuật có hiểu mỗi màn hình, tìm được thứ cần tìm, mở đúng đoạn nguyên văn, dùng không cần học không? Mỗi phần tử có làm được offline trên CPU trong lộ trình không (ánh xạ P1, P2, P3, P4, hay mới), có hứa điều app không làm được (vd chữ do AI viết hiện như trích dẫn, kết luận hiệu lực mà không có người xác nhận)? Nhãn tiếng Việt có đơn giản và đúng? Đường đi bằng bàn phím và đọc màn hình? Điều khiển thử bằng Playwright cho Node để kiểm tương tác chạy thật. Báo tối đa 12 vấn đề kèm bằng chứng.` },
]
const reviews = await parallel(LENS_REVIEW.map(l => () => agent(
  `${CONTEXT}\n\nTệp mẫu: ${OUT}. CHỈ ĐỌC: không sửa tệp, không commit. Mỗi vấn đề cần bằng chứng cụ thể (tên ảnh, selector, số đo, dòng mã); bỏ góp ý thẩm mỹ chung chung. Máy chủ nào bạn bật thì ghi PID vào tệp rồi kill theo PID, không pkill -f.\n\n${l.prompt}`,
  { label: `soat:${l.key}`, phase: 'Soát', schema: ISSUES })))
const issues = reviews.flatMap((r, i) => r ? r.issues.map((x, j) => ({ ...x, id: `${LENS_REVIEW[i].key}-${j + 1}` })) : [])
if (reviews.some(r => !r)) log('MỘT NGƯỜI SOÁT MẤT KẾT QUẢ: danh sách vấn đề chưa đủ')
log(`soát: ${issues.length} vấn đề`)

phase('Sửa')
const fixed = issues.length ? await agent(`${CONTEXT}\n\nÁp các phát hiện soát lên mẫu ${OUT} (brief: ${BRIEF}). Với từng vấn đề: TRƯỚC HẾT cố bác bỏ nó (xem tệp và dựng ảnh lại: sai, đã đúng sẵn, hay chỉ là sở thích thì bỏ qua kèm một dòng lý do); vấn đề thật thì sửa nhỏ nhất. Rồi chụp lại: \`NODE_PATH=$(npm root -g) node ${shoot} ${OUT} ${SP}/shots-final\` cùng các trạng thái chính, mở từng ảnh bằng Read; overflowX = 0, một h1 mỗi màn hình, không lỗi console. Không sửa tệp nào khác của repo, không commit. Trả bảng: id, đã sửa/bỏ qua, một dòng ghi chú; rồi đường dẫn ảnh cuối.\n\nVẤN ĐỀ:\n${JSON.stringify(issues, null, 1)}`,
  { label: 'sua', phase: 'Sửa' }) : 'không có vấn đề cần sửa'

return { brief: BRIEF, prototype: OUT, research: research.map(r => ({ lens: r.lens, top: r.top_recommendations })), build, issues: issues.map(i => ({ id: i.id, severity: i.severity, where: i.where, problem: i.problem })), fixed }
