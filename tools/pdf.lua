--[[ Filter for the PDF edition (_quarto-pdf.yml); the website does not use it.

  * Collapsed "Answer" callouts would print each answer right under its
    example. They are moved to an "Answers" section at the end of each
    chapter, and the example gets a link "Answer k" to it.
  * <font color="..."> ... </font> becomes \textcolor{...}{...}, and the text
    stand-in of a web-only output (an animation video) is dropped.
  * Links to files of the site (solution PDFs, ...) and references to the
    appendices, which are not in the PDF, point to the published site.
  * Font-size commands such as \scriptsize and blank lines are dropped inside
    math, where LaTeX does not allow them.
]]

local SITE = 'https://seoultechpse.github.io/EngMath/'

-- appendix section id -> {url, title}, read from the appendix sources
local appendix = {}
local function read_appendices()
  local p = io.popen('ls x_*.qmd 2>/dev/null')
  for file in p:lines() do
    local page = SITE .. file:gsub('%.qmd$', '.html')
    for line in io.lines(file) do
      local hashes, title, id = line:match('^(#+)%s+(.-)%s*{#(sec%-[%w%-]+)')
      if id then
        appendix[id] = { url = (#hashes == 1) and page or (page .. '#' .. id),
                         title = title:gsub('%$[~\\,]+%$', ''):gsub('^%s+', '') }
      end
    end
  end
  p:close()
end
read_appendices()

local SIZES = { 'tiny', 'scriptsize', 'footnotesize', 'small', 'normalsize',
                'large', 'Large', 'LARGE', 'huge', 'Huge' }

local function is_answer(div)
  return div.classes:includes('callout-note') and div.attributes['title'] == 'Answer'
end

-- <font color=...> ... </font> within one list of inlines
local function font_colors(inlines)
  local out, stack = pandoc.Inlines{}, {}
  for _, el in ipairs(inlines) do
    if el.t == 'RawInline' and el.format == 'html' then
      local color = el.text:match('^<font%s+color%s*=%s*["\']?(%a+)')
      if color then
        table.insert(stack, #out)
        out:insert(pandoc.RawInline('latex', '\\textcolor{' .. color .. '}{'))
        goto continue
      elseif el.text:match('^</font>') then
        if #stack > 0 then
          table.remove(stack)
          out:insert(pandoc.RawInline('latex', '}'))
        end
        goto continue
      elseif el.text:match('^<font') then        -- <font size=...>: drop
        goto continue
      end
    end
    out:insert(el)
    ::continue::
  end
  for _ = 1, #stack do out:insert(pandoc.RawInline('latex', '}')) end   -- unclosed tags
  return out
end

local function absolute(target)
  if target:match('^%a[%w+.-]*:') or target:match('^#') then return target end
  local file = target:match('^([^#]+)')
  if file and (file:match('^files/') or file:match('^figures/') or file:match('^x_')) then
    return SITE .. target:gsub('^x_(.-)%.qmd', 'x_%1.html')
  end
  return target
end

local inline_filter = {
  Inlines = font_colors,
  Math = function(m)
    for _, size in ipairs(SIZES) do
      m.text = m.text:gsub('\\' .. size .. '(%A)', '%1')
    end
    -- MathJax accepts blank lines inside display math; LaTeX does not
    m.text = m.text:gsub('\n[ \t]*\n', '\n')
    return m
  end,
  Str = function(s)
    -- characters the PDF fonts lack: em space, emoji
    local t = s.text:gsub('\u{2003}', ' '):gsub('\u{1F9E9}%s*', '')
    if t ~= s.text then return pandoc.Str(t) end
  end,
  Link = function(l) l.target = absolute(l.target); return l end,
  -- text stand-in for a web-only output (the animation videos)
  CodeBlock = function(cb)
    if cb.text:match('^<IPython%.core%.display%.%w+ object>%s*$') then return {} end
  end,
  Cite = function(c)
    local id = c.citations[1].id
    local a = appendix[id]
    if a and #c.citations == 1 then
      return pandoc.Link(a.title, a.url)
    end
  end,
}

-- move the Answer callouts of each chapter to its end
function Pandoc(doc)
  local blocks, out = doc.blocks, pandoc.Blocks{}
  local answers, chapter, section, k, pending = {}, 'chapter', nil, 0, nil

  local function flush()
    if #answers == 0 then return end
    out:insert(pandoc.Header(2, 'Answers', pandoc.Attr('', { 'unnumbered' })))
    for _, a in ipairs(answers) do
      local head = pandoc.Inlines{ pandoc.Strong('Answer ' .. a.k) }
      if a.section then
        head:insert(pandoc.Str(' ('))
        head:insert(pandoc.Cite({ pandoc.Str('@' .. a.section) },
                                { pandoc.Citation(a.section, 'NormalCitation') }))
        head:insert(pandoc.Str(')'))
      end
      local body = pandoc.Blocks{ pandoc.Para(head) }
      body:extend(a.content)
      out:insert(pandoc.Div(body, pandoc.Attr(a.id)))
    end
    answers = {}
  end

  for _, b in ipairs(blocks) do
    if b.t == 'Header' and b.level == 1 then
      flush()
      chapter, k, section = (b.identifier ~= '' and b.identifier or chapter), 0, nil
      out:insert(b)
    elseif b.t == 'Header' and b.level == 2 then
      section = b.identifier:match('^sec%-') and b.identifier or section
      out:insert(b)
    elseif b.t == 'Div' and is_answer(b) then
      k = k + 1
      local id = 'ans-' .. chapter .. '-' .. k
      table.insert(answers, { k = k, id = id, section = section, content = b.content })
      pending = pandoc.Inlines{ pandoc.Emph{ pandoc.Link('Answer ' .. k, '#' .. id) },
                                pandoc.Str(' (end of chapter)') }
    else
      if pending then
        -- put "Answer k" on the line of the [Solution] link that follows it
        local first = b.t == 'Para' and b.content[1]
        if first and first.t == 'Link' and pandoc.utils.stringify(first) == 'Solution' then
          pending:extend{ pandoc.Space(), pandoc.Str('·'), pandoc.Space() }
          pending:extend(b.content)
          b = pandoc.Para(pending)
        else
          out:insert(pandoc.Para(pending))
        end
        pending = nil
      end
      out:insert(b)
    end
  end
  if pending then out:insert(pandoc.Para(pending)) end
  flush()
  doc.blocks = out
  return doc:walk(inline_filter)
end
