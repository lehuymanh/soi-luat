export const meta = {
  name: 'review-lenses',
  description: 'Soát độc lập một dải commit theo nhiều góc nhìn, rồi mỗi góc có một người hoài nghi cố bác bỏ từng phát hiện; trả về danh sách đã xác nhận. Chỉ đọc, không sửa mã.',
  whenToUse: 'Sau khi xong một bước hay một đợt mã, trước khi sửa và trước khi push. Tham số và ví dụ: docs/quy-trinh.md, mục "Workflow có sẵn".',
  phases: [
    { title: 'Tìm', detail: 'mỗi góc nhìn một người soát, chỉ đọc' },
    { title: 'Bác bỏ', detail: 'mỗi góc nhìn một người hoài nghi chạy lại từng phát hiện' },
  ],
}

// Tham số (args): range hoặc commits (bắt buộc một trong hai); lenses, paths, context, fixed, rejected,
// python, pytest, scratch, maxFindings. Ý nghĩa từng tham số: docs/quy-trinh.md.
const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const need = (ok, msg) => { if (!ok) throw new Error('review-lenses: ' + msg) }

const MAX_LENSES = 5
const LIB = {
  bugs: 'GÓC NHÌN LỖI. Kết quả sai, sập, ca biên (rỗng, 0, phần tử cuối, làm tròn, chữ có dấu), nơi gọi bị hỏng vì đổi chữ ký hoặc giá trị trả về (grep mọi nơi gọi, kể cả bench/, tests/, mẫu HTML, JS), hàm dùng chung vẫn sai, hai nơi áp một quy tắc theo hai cách.',
  tests: 'GÓC NHÌN TEST, AN TOÀN, TỐC ĐỘ. (1) Logic rủi ro mới mà không test nào hỏng khi nó hỏng: nêu đúng hành vi và test cần có. (2) Dữ liệu không tin cậy (chữ OCR, tên tệp, đầu ra mô hình, tham số URL) đi vào regex, JSON, HTML, SQL, đường dẫn mà không kiểm. (3) Regex backtrack hay O(n^2) trên dòng OCR dài (Điều 64.000 ký tự, dòng 10.000 ký tự); truy vấn từng mục trong vòng lặp ở kho 61 nghìn Điều; việc lặp mỗi lần gọi mà tính một lần được. Nói chậm chỉ khi đã đo bằng đoạn mã ngắn.',
  security: 'GÓC NHÌN BẢO MẬT VÀ RANH GIỚI TIN CẬY. Mọi route (GET và POST): CSRF, Host guard, kiểm tham số, đường dẫn tệp (nạp, /page, sao lưu, xuất); chữ của văn bản, tên tệp, câu hỏi, tên cuộc trò chuyện đi vào HTML hay JS (innerHTML, |safe, thuộc tính, href); lệnh con (LibreOffice, Word COM, tesseract) với tên tệp làm đối số; zip và docx (bom nén, XXE); thứ trang web khác trong trình duyệt người dùng chạm được (DNS rebinding, CSRF qua form, CORS). Thử bằng TestClient hoặc đoạn mã ngắn với tải trọng thật.',
  data: 'GÓC NHÌN AN TOÀN DỮ LIỆU VÀ ĐỒNG THỜI. Giao dịch nạp, dựng lại, xoá; nâng cấp dữ liệu một lần; gợi ý hiệu lực và liên kết đã duyệt có còn nguyên; hai bản app dùng một kho; app bị tắt giữa lúc ghi; đĩa đầy; khoá ghi giữ quá lâu làm tìm hay lưu bị treo; bộ nhớ tăng trong phiên dài; luồng nền chết im.',
  ui: 'GÓC NHÌN GIAO DIỆN, TRUY CẬP VÀ HỒI QUY. Chạy app trên kho thử bằng Playwright cho Node (NODE_PATH=$(npm root -g)) ở 1440, 900, 390, sáng và tối: bộ xử lý sự kiện gắn hai lần sau khi đổi nội dung, quản lý focus và Esc (hộp thoại, ngăn kéo, lớp phủ), id trùng khi có nhiều câu trả lời, bàn phím và đọc màn hình, CSS bị xoá mà trang khác còn dùng (grep các template), lỗi console, cuộn ngang. Mỗi phát hiện cần bằng chứng: tên ảnh, selector, số đo. Dừng máy chủ theo PID đã lưu, không dùng pkill -f.',
  lean: 'GÓC NHÌN GỌN. Mã không nên tồn tại hay nên ngắn hơn: mã chết, tham số hay tuỳ chọn không ai dùng (grep cả cây: src, tests, bench, pack, mau, template, JS trước khi gọi là không dùng), hàm trùng với hàm có sẵn trong repo (nêu cả hai đường dẫn), bản sao gần giống phải đổi cùng nhau, tầng bọc chỉ chuyển tiếp, thư viện làm việc vài dòng làm được. Nêu đúng các dòng xoá được và số dòng ròng.',
}

function pickLenses(spec, fallback) {
  const list = (spec && spec.length ? spec : fallback).map(x => {
    if (typeof x === 'string') { need(LIB[x], `không có góc nhìn "${x}"; có sẵn: ${Object.keys(LIB).join(', ')}`); return { key: x, prompt: LIB[x] } }
    need(x && x.key && x.prompt, 'góc nhìn tự định nghĩa cần {key, prompt}')
    return x
  })
  need(list.length <= MAX_LENSES, `tối đa ${MAX_LENSES} góc nhìn (mỗi góc 2 agent); chia làm hai lần chạy`)
  need(new Set(list.map(l => l.key)).size === list.length, 'key góc nhìn bị trùng')
  return list
}

need(A.range || (A.commits && A.commits.length), 'cần args.range (vd "abc1234..HEAD") hoặc args.commits (danh sách hash)')
const lenses = pickLenses(A.lenses, ['bugs', 'tests', 'lean'])
const py = A.python || 'python'
const pytest = A.pytest || `${py} -m pytest -q`
const maxFindings = A.maxFindings || 8
const scratch = A.scratch ? `Script thử viết trong ${A.scratch} (mkdir -p), không viết vào repo.` : 'Script thử viết trong thư mục scratchpad của phiên, không viết vào repo.'
const where = A.paths && A.paths.length ? ` -- ${A.paths.join(' ')}` : ''
const scope = A.range
  ? `dải git ${A.range}: chạy \`git diff ${A.range} --stat${where}\` rồi \`git diff ${A.range}${where || ' -- <tệp>'}\``
  : `các commit ${A.commits.join(', ')}: chạy \`git show --stat <hash>\` rồi \`git show <hash>${where}\` cho từng commit (chỉ xét các commit này, kể cả khi cây còn commit khác của agent khác)`
const already = [
  A.fixed ? `Đã sửa trong phạm vi này (đừng báo lại): ${A.fixed}` : '',
  A.rejected ? `Đã soát và bác bỏ vì là hành vi chủ ý (đừng báo lại trừ khi có ca hỏng MỚI): ${A.rejected}` : '',
].filter(Boolean).join('\n')

const COMMON = `${A.context || 'Repo hiện tại là Soi Luật: app tra cứu văn bản pháp luật Việt Nam chạy offline cho một người dùng trên 127.0.0.1 (FastAPI, Jinja, JS thuần, SQLite FTS5). Bản đồ module: docs/kien-truc.md.'}

Phạm vi soát: ${scope}.
Đọc mã đổi VÀ nơi gọi nó VÀ mã nó gọi; đừng tin thông điệp commit.
${already}
LUẬT: chỉ đọc. Không sửa tệp, không commit, không chạy máy chủ hay bộ đo dài, không pkill -f. Được chạy \`${pytest} <tệp test liên quan>\` và đoạn Python ngắn (PYTHONPATH=src, dùng \`${py}\`). ${scratch}
Mỗi phát hiện cần MỘT TÌNH HUỐNG CỤ THỂ (đầu vào hay trạng thái này dẫn tới kết quả sai này) mà bạn đã chạy lại hoặc lần theo mã. Không có tình huống thì không báo. Không góp ý văn phong, không "nên cân nhắc".
Mức: must = lỗi, hố bảo mật, mất dữ liệu, hỏng ở tải dự kiến; should = logic rủi ro chưa có test, chậm thật, trùng lặp, mã không nên tồn tại; nice = nhỏ. Viết bằng tiếng Việt ngắn, từ thường.`

const FIND = { type: 'object', properties: { findings: { type: 'array', items: { type: 'object', properties: {
  title: { type: 'string' }, file: { type: 'string' }, lines: { type: 'string' },
  group: { type: 'string', enum: ['must', 'should', 'nice'] },
  scenario: { type: 'string', description: 'đầu vào hay trạng thái cụ thể dẫn tới kết quả sai' },
  evidence: { type: 'string', description: 'đoạn mã đã chạy hay đường mã đã lần theo' },
  fix: { type: 'string', description: 'sửa nhỏ nhất, ưu tiên xoá mã' } },
  required: ['title', 'file', 'lines', 'group', 'scenario', 'fix'] } },
  not_read: { type: 'string', description: 'phần bạn chưa đọc' } }, required: ['findings'] }
const VERDICTS = { type: 'object', properties: { verdicts: { type: 'array', items: { type: 'object', properties: {
  id: { type: 'string' }, confirmed: { type: 'boolean' }, group: { type: 'string', enum: ['must', 'should', 'nice'] },
  reason: { type: 'string' }, reproduction: { type: 'string' }, fix: { type: 'string' } },
  required: ['id', 'confirmed', 'group', 'reason'] } } }, required: ['verdicts'] }

log(`review-lenses: ${lenses.length} góc nhìn, tối đa ${lenses.length * 2} agent`)

const results = await pipeline(
  lenses,
  l => agent(`${COMMON}\n\n${l.prompt}\n\nBáo tối đa ${maxFindings} phát hiện, quan trọng nhất trước. Nói rõ phần nào bạn chưa đọc.`,
    { label: `tim:${l.key}`, phase: 'Tìm', schema: FIND }),
  (found, l) => {
    if (!found) return { key: l.key, failed: 'tim', list: [], verdicts: [] }
    const list = found.findings.map((f, i) => ({ ...f, id: `${l.key}-${i + 1}` })) // id gán bằng mã, không tin mô hình
    if (!list.length) return { key: l.key, list, verdicts: [], not_read: found.not_read || '' }
    return agent(`${COMMON}\n\nBạn là người hoài nghi độc lập cho góc nhìn "${l.key}". Với TỪNG phát hiện dưới đây, cố BÁC BỎ: đọc lại đúng các dòng ở HEAD, grep mọi nơi gọi và chỗ nhắc tên, xem nơi khác đã chặn chưa, chạy lại tình huống bằng script ngắn. confirmed=false là mặc định khi bạn không chỉ ra được lỗi cụ thể. Xếp lại nhóm theo tải dự kiến. Với cái đúng, ghi cách sửa nhỏ nhất. Không thêm phát hiện mới. Trả đúng một phán quyết cho mỗi id.\n\nPHÁT HIỆN:\n${JSON.stringify(list, null, 1)}`,
      { label: `bacbo:${l.key}`, phase: 'Bác bỏ', schema: VERDICTS })
      .then(v => ({ key: l.key, failed: v ? '' : 'bacbo', list, verdicts: v ? v.verdicts : [], not_read: found.not_read || '' }))
  },
)

const ORDER = { must: 0, should: 1, nice: 2 }
const confirmed = [], rejected = [], unverified = [], failed = [], notRead = []
for (const r of results.filter(Boolean)) {
  if (r.failed) failed.push(`${r.key}:${r.failed}`)
  if (r.not_read) notRead.push({ lens: r.key, not_read: r.not_read })
  for (const f of r.list) {
    const v = r.verdicts.find(x => x.id === f.id)
    const item = { lens: r.key, id: f.id, title: f.title, file: f.file, lines: f.lines, group: v ? v.group : f.group, scenario: f.scenario }
    if (!v) unverified.push(item)
    else if (v.confirmed) confirmed.push({ ...item, fix: v.fix || f.fix, reason: v.reason, reproduction: v.reproduction || '' })
    else rejected.push({ ...item, reason: v.reason })
  }
}
confirmed.sort((a, b) => ORDER[a.group] - ORDER[b.group])
const lost = lenses.length - results.filter(Boolean).length
if (lost) failed.push(`${lost} góc nhìn mất kết quả`)
log(`xác nhận ${confirmed.length}, bác bỏ ${rejected.length}, chưa có phán quyết ${unverified.length}${failed.length ? `; LỖI: ${failed.join(', ')}` : ''}`)

return { scope: A.range || A.commits, confirmed, rejected, unverified, failed, not_read: notRead }
