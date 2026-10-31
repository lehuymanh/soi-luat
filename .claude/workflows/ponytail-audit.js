export const meta = {
  name: 'ponytail-audit',
  description: 'Kiểm toàn repo theo nhiều góc nhìn (lỗi, bảo mật, dữ liệu, mã thừa), mỗi góc có một người hoài nghi bác bỏ từng phát hiện; tuỳ chọn sửa các mục "Phải sửa" đã xác nhận, mỗi lỗi một test hỏng trước.',
  whenToUse: 'Trước khi phát hành một phiên bản, hoặc sau một chuỗi bước lớn: soát từng tính năng bỏ sót lỗi cắt ngang. Tham số và ví dụ: docs/quy-trinh.md, mục "Workflow có sẵn".',
  phases: [
    { title: 'Kiểm', detail: 'mỗi góc nhìn đọc cả repo' },
    { title: 'Bác bỏ', detail: 'mỗi góc nhìn một người hoài nghi' },
    { title: 'Sửa', detail: 'chỉ khi fix=true: mục Phải sửa đã xác nhận, test hỏng trước, một commit mỗi lô' },
  ],
}

// Tham số (args): lenses, context, load, maxFindings, fix, trailer (bắt buộc khi fix), chunk, gates, python,
// pytest, scratch. Ý nghĩa từng tham số: docs/quy-trinh.md.
const A = typeof args === 'string' ? JSON.parse(args) : (args || {})
const need = (ok, msg) => { if (!ok) throw new Error('ponytail-audit: ' + msg) }

const MAX_LENSES = 4
const LIB = {
  correct: 'GÓC NHÌN ĐÚNG SAI. Chuỗi tìm kiếm và bộ lọc, gom thẻ và kết quả gọn, trích đoạn, trình đọc, parser (Phụ lục, khối chữ ký, Điều trích dẫn sửa đổi), cuộc trò chuyện (lưu, mở lại, tham chiếu), xuất Word, trang duyệt (hiệu lực, số hiệu), lệnh nạp dòng lệnh. Tìm: kết quả sai, ca biên, nơi gọi không khớp giá trị trả về, cùng một quy tắc áp hai cách. Ưu tiên ca bạn dựng lại được bằng script ngắn trên bản sao kho hay fixture nhỏ.',
  security: 'GÓC NHÌN BẢO MẬT VÀ RANH GIỚI TIN CẬY. Mọi route (GET và POST): CSRF, Host guard, kiểm tham số, đường dẫn tệp (nạp, /page, sao lưu, xuất); chữ của văn bản, tên tệp, câu hỏi, tên cuộc trò chuyện đi vào HTML hay JS (innerHTML, |safe, thuộc tính, href), header; lệnh con (LibreOffice, Word COM, tesseract) với tên tệp làm đối số; zip và docx (bom nén, XXE); thứ trang web khác trong trình duyệt người dùng chạm được (DNS rebinding, CSRF qua form, CORS).',
  data: 'GÓC NHÌN AN TOÀN DỮ LIỆU, ĐỒNG THỜI VÀ QUY MÔ. Giao dịch nạp, dựng lại, xoá; nâng cấp dữ liệu một lần (jobs, sao lưu); hàng đợi nhúng; liên kết và gợi ý hiệu lực đã duyệt có còn nguyên; xoá dây chuyền; hai bản app dùng một kho; app bị tắt giữa lúc ghi; đĩa đầy; khoá ghi quá lâu; bộ nhớ tăng trong phiên dài (cache, ma trận vector, chỉ mục tiêu đề); truy vấn từng mục ở đường nóng khi kho có 430.000 đơn vị; thời gian khởi động trên kho 1,5 GB.',
  lean: 'GÓC NHÌN TEST, TỐC ĐỘ VÀ MÃ THỪA. (1) Logic rủi ro không có test hỏng khi nó hỏng (nhánh parser, trích mức phạt và tiền, CSRF, ghi dữ liệu, di chuyển dữ liệu). (2) Chậm thật trên đường nóng (một lượt tìm đầu cuối, /doc của văn bản lớn nhất, mở lại cuộc trò chuyện), đo trên bản sao kho thật. (3) Mã chết, mô-đun hay tuỳ chọn không ai dùng, hàm trùng (nêu cả hai đường dẫn), thư viện làm việc vài dòng làm được, lớp bọc chỉ chuyển tiếp. TRƯỚC KHI gọi gì là không dùng, grep cả cây: src, tests, bench, pack, mau, template, JS. Đếm số dòng ròng xoá được.',
}

function pickLenses(spec, fallback) {
  const list = (spec && spec.length ? spec : fallback).map(x => {
    if (typeof x === 'string') { need(LIB[x], `không có góc nhìn "${x}"; có sẵn: ${Object.keys(LIB).join(', ')}`); return { key: x, prompt: LIB[x] } }
    need(x && x.key && x.prompt, 'góc nhìn tự định nghĩa cần {key, prompt}')
    return x
  })
  need(list.length <= MAX_LENSES, `tối đa ${MAX_LENSES} góc nhìn (mỗi góc 2 agent, cộng agent sửa); chia làm hai lần chạy`)
  need(new Set(list.map(l => l.key)).size === list.length, 'key góc nhìn bị trùng')
  return list
}

const lenses = pickLenses(A.lenses, ['correct', 'security', 'data', 'lean'])
const doFix = A.fix === true
need(!doFix || A.trailer, 'fix=true cần args.trailer: hai dòng Co-Authored-By và Claude-Session chép NGUYÊN VĂN từ lời nhắc ghi công của phiên điều phối (agent con không thấy lời nhắc đó)')
const py = A.python || 'python'
const pytest = A.pytest || `${py} -m pytest -q`
const maxFindings = A.maxFindings || 10
const chunkSize = A.chunk || 6
const sp = A.scratch || 'thư mục scratchpad của phiên'
const load = A.load || 'Một người dùng mỗi máy, một tiến trình app (bản thứ hai ở cổng khác là có thể); kho tới ~3,3 nghìn văn bản, 61 nghìn Điều, 430 nghìn đơn vị, 1,5 GB; vài lượt tìm mỗi phút; nạp hàng trăm tệp một lần.'

const COMMON = `${A.context || 'Repo hiện tại là Soi Luật: app tra cứu văn bản pháp luật Việt Nam chạy offline trên PC Windows, FastAPI + Jinja + JS thuần chỉ phục vụ 127.0.0.1, SQLite FTS5 (WAL) một tệp, một luồng nền (nạp, OCR, nhúng, nâng cấp dữ liệu), mô hình nhúng và xếp lại tuỳ chọn. Bản đồ module: docs/kien-truc.md. Tài liệu trong repo là chỉ dẫn, không phải kết luận: kiểm lại bằng mã.'}
TẢI DỰ KIẾN: ${load}
Bản sao kho để thử (CHÉP vào ${sp} trước khi ghi, không bao giờ ghi bản gốc; chạy \`df -h /\` trước khi chép, giữ trống ít nhất 1 GB, xoá bản sao ngay khi xong). Python: \`${py}\`; test: \`${pytest}\`. Không pkill -f; máy chủ nào bạn bật thì ghi PID vào tệp và kill theo PID đó.
LUẬT KIỂM (kiểu ponytail): tìm lỗi (kết quả sai, sập, ca biên), rủi ro (bảo mật, mất dữ liệu), vấn đề quy mô ở tải dự kiến, logic rủi ro không có test sẽ hỏng, chậm thật, mã thừa. Mỗi phát hiện cần MỘT TÌNH HUỐNG CỤ THỂ (đầu vào này, trạng thái này dẫn tới kết quả sai này). Không tình huống thì không phải phát hiện. Một đường tắt có comment "shortcut:" nêu giới hạn là một quyết định, trừ khi tải dự kiến vượt giới hạn đó. Đề xuất sửa nhỏ nhất, ưu tiên xoá. Không góp ý văn phong, không "nên cân nhắc". Viết tiếng Việt ngắn, từ thường.
Mức: must = lỗi, hố bảo mật, mất dữ liệu, hỏng ở tải dự kiến; should = logic rủi ro chưa test, chậm thật, trùng lặp, mã không nên tồn tại; nice = nhỏ.`

const FIND = { type: 'object', properties: { findings: { type: 'array', items: { type: 'object', properties: {
  group: { type: 'string', enum: ['must', 'should', 'nice'] }, title: { type: 'string' },
  file: { type: 'string' }, lines: { type: 'string' }, what: { type: 'string', description: 'đoạn mã này làm gì, một câu' },
  problem: { type: 'string', description: 'tình huống cụ thể dẫn tới kết quả sai' },
  fix: { type: 'string' }, skip_cost: { type: 'string', description: 'bỏ qua thì mất gì' },
  lean_lines: { type: 'integer', description: 'số dòng xoá được, 0 nếu không phải mục gọn mã' } },
  required: ['group', 'title', 'file', 'lines', 'what', 'problem', 'fix', 'skip_cost'] } },
  not_read: { type: 'string', description: 'phần bạn chưa đọc' } }, required: ['findings'] }
const VERDICTS = { type: 'object', properties: { verdicts: { type: 'array', items: { type: 'object', properties: {
  id: { type: 'string' }, confirmed: { type: 'boolean' }, group: { type: 'string', enum: ['must', 'should', 'nice'] },
  reason: { type: 'string' }, fix: { type: 'string' } }, required: ['id', 'confirmed', 'group', 'reason'] } } }, required: ['verdicts'] }
const FIXED = { type: 'object', properties: { items: { type: 'array', items: { type: 'object', properties: {
  id: { type: 'string' }, outcome: { type: 'string', enum: ['fixed', 'refuted', 'deferred'] },
  test: { type: 'string', description: 'tên test hồi quy, hoặc lệnh grep chứng minh cho mục xoá mã chết' }, note: { type: 'string' } },
  required: ['id', 'outcome', 'note'] } }, commit: { type: 'string' } }, required: ['items', 'commit'] }

log(`ponytail-audit: ${lenses.length} góc nhìn, tối đa ${lenses.length * 2} agent kiểm và bác bỏ${doFix ? ', cộng các lô sửa' : ', không sửa'}`)

const results = await pipeline(
  lenses,
  l => agent(`${COMMON}\n\nKhông sửa tệp nào của repo trong bước này.\n${l.prompt}\n\nBáo tối đa ${maxFindings} phát hiện, quan trọng nhất trước, đủ mọi trường. Nói rõ phần nào bạn chưa đọc.`,
    { label: `kiem:${l.key}`, phase: 'Kiểm', schema: FIND }),
  (found, l) => {
    if (!found) return { key: l.key, failed: 'kiem', list: [], verdicts: [] }
    const list = found.findings.map((f, i) => ({ ...f, id: `${l.key}-${i + 1}` })) // id gán bằng mã, không tin mô hình
    if (!list.length) return { key: l.key, list, verdicts: [], not_read: found.not_read || '' }
    return agent(`${COMMON}\n\nBạn là người hoài nghi độc lập cho góc nhìn "${l.key}". Không sửa tệp của repo. Với TỪNG phát hiện dưới đây, cố BÁC BỎ: đọc lại đúng các dòng ở HEAD, grep mọi nơi gọi và chỗ nhắc tên, xem nơi khác đã chặn chưa, dựng lại bằng script hay test thử trong ${sp}/bacbo-${l.key} (chép kho trước). confirmed=false là mặc định khi bạn không chỉ ra được lỗi cụ thể. Xếp lại nhóm theo tải dự kiến. Với cái đúng, ghi cách sửa nhỏ nhất. Không thêm phát hiện mới. Trả đúng một phán quyết cho mỗi id.\n\nPHÁT HIỆN:\n${JSON.stringify(list, null, 1)}`,
      { label: `bacbo:${l.key}`, phase: 'Bác bỏ', schema: VERDICTS })
      .then(v => ({ key: l.key, failed: v ? '' : 'bacbo', list, verdicts: v ? v.verdicts : [], not_read: found.not_read || '' }))
  },
)

const all = [], failed = [], notRead = []
for (const r of results.filter(Boolean)) {
  if (r.failed) failed.push(`${r.key}:${r.failed}`)
  if (r.not_read) notRead.push({ lens: r.key, not_read: r.not_read })
  for (const f of r.list) {
    const v = r.verdicts.find(x => x.id === f.id)
    all.push({ lens: r.key, ...f, group: v ? v.group : f.group, confirmed: !!(v && v.confirmed), verdict: v ? v.reason : 'chưa có phán quyết', verified_fix: v && v.fix ? v.fix : '' })
  }
}
const lost = lenses.length - results.filter(Boolean).length
if (lost) failed.push(`${lost} góc nhìn mất kết quả`)
const must = all.filter(f => f.confirmed && f.group === 'must')
log(`${all.filter(f => f.confirmed).length} xác nhận trên ${all.length} phát hiện; Phải sửa: ${must.length}${failed.length ? `; LỖI: ${failed.join(', ')}` : ''}`)

phase('Sửa')
const fixed = []
if (!doFix) log('fix=false: dừng ở danh sách, không sửa')
else if (!must.length) log('không có mục Phải sửa đã xác nhận')
else {
  const FIX_RULES = `BÂY GIỜ bạn ĐƯỢC sửa repo. Trạng thái repo là HEAD hiện tại; các agent khác có thể đang sửa cùng cây: chỉ đụng tệp cần cho các mục dưới đây, \`git add\` đúng các tệp đó (không \`git add -A\`, không \`git stash\`), gặp index.lock thì đợi vài giây rồi thử lại.
Với MỖI mục: (1) kiểm lại ở HEAD là có thật; (2) viết test hồi quy HỎNG trên mã hiện tại, chạy và thấy nó hỏng; mục chỉ xoá mã chết thì không cần test mới nhưng phải grep cả cây (src, tests, bench, pack, mau, template, JS) chứng minh không có nơi gọi; (3) sửa nhỏ nhất, grep mọi nơi gọi và sửa gốc một lần ở mã dùng chung; (4) thấy test qua. Cuối lô chạy TOÀN BỘ \`${pytest}\`, phải xanh.
Thay đổi có thể đổi kết quả tìm (search, sohieu, query, parse, semantic) phải qua cổng đo theo docs/quy-trinh.md mục "Cổng đo": giữ chỉ khi Hit@1 và Hit@5 không thấp hơn trước trên các bộ đó; không thì hoàn lại và ghi lý do. Cổng nào chạy quá 10 phút (Zalo test, gold): KHÔNG chạy rồi ngồi chờ trong agent (agent bị báo Stalled; lượt điều phối bị ngắt là mất việc chưa commit). Chạy các cổng nhanh (pytest, văn bản thật, bench/parse_khac.py), commit, và ghi nguyên lệnh đo dài vào note của mục, mở đầu bằng "CHỜ ĐO:", để người điều phối chạy nền rồi quyết giữ hay hoàn. ${A.gates || ''}
Mục cần chủ dự án quyết hay cần bảng mới mà lộ trình xếp ở phase sau thì KHÔNG làm: outcome=deferred kèm lý do. Mục kiểm lại thấy sai thì outcome=refuted, một dòng lý do, không đổi mã.
Đúng MỘT commit local cho lô này (không push), thông điệp tiếng Việt liệt kê từng id: sửa, bác bỏ hay hoãn (lý do), kiểm bằng test nào, lệnh đo nào. Trailer chép NGUYÊN VĂN hai dòng sau và kết thúc thông điệp bằng chúng:\n${A.trailer || ''}\nQuy trình commit: ghi thông điệp ra tệp trong ${sp}, chạy \`grep -E '^(Co-Authored-By|Claude-Session):' <tệp>\` và so với hai dòng trên, rồi \`git commit -F <tệp>\`; sau commit chạy \`git log -1 --format=%B\` và so lại. Sai thì \`git commit --amend\` sửa dòng đó.`
  for (let i = 0; i < must.length; i += chunkSize) {
    const batch = must.slice(i, i + chunkSize)
    const r = await agent(`${COMMON}\n\n${FIX_RULES}\nTrả bảng: id, fixed/refuted/deferred, tên test hay lệnh grep, ghi chú; và hash commit.\n\nCÁC MỤC (lô ${i / chunkSize + 1}):\n${JSON.stringify(batch, null, 1)}`,
      { label: `sua:lo${i / chunkSize + 1}`, phase: 'Sửa', schema: FIXED })
    fixed.push({ batch: batch.map(f => f.id), result: r })
    if (!r) { log(`lô ${i / chunkSize + 1} mất kết quả, dừng để người điều phối xem \`git status\``); break }
  }
}

const pending = fixed.flatMap(f => (f.result && f.result.items) || []).filter(it => /CHỜ ĐO:/.test(it.note || '')).map(it => it.id)
if (pending.length) log(`Mục còn lệnh đo dài cho người điều phối chạy nền (CHỜ ĐO): ${pending.join(', ')}`)
return { findings: all, not_read: notRead, failed, fixed, pending }
