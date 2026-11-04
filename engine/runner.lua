-- Headless platform adapter only; upstream calculation/data files stay unchanged.
local inputPath = assert(arg[1], "Input XML path required")
local metadataPath = assert(arg[2], "Metadata path required")
local originalLoadfile = loadfile
function loadfile(path)
 local f = io.open(path, 'rb')
 if not f then return originalLoadfile(path) end
 local source = f:read('*a'); f:close()
 if source:sub(1, 2) == '#@' then
  return loadstring(source:gsub('^#[^\n]*', ''), '@' .. path)
 end
 return originalLoadfile(path)
end
function dofile(path) return assert(loadfile(path))() end
local logs = {}
print = function(...)
 local parts = {}
 for i = 1, select('#', ...) do parts[i] = tostring(select(i, ...)) end
 logs[#logs + 1] = table.concat(parts, ' ')
end
-- The desktop wrapper contains UI stubs. Calculations and parsers are unmodified.
dofile('HeadlessWrapper.lua')
assert(not __mainObject__.promptMsg, __mainObject__.promptMsg)
local json = require('dkjson')
local f = assert(io.open(inputPath, 'rb')); local xml = f:read('*a'); f:close()
local m = assert(io.open(metadataPath, 'rb')); local request = assert(json.decode(m:read('*a'))); m:close()
assert(not xml:find('<PlayerStat[%s/>]'), 'Saved totals must be stripped before calculation')
loadBuildFromXML(xml, 'Build Lab')
local player = build.calcsTab.calcsEnv.player
local output = build.calcsTab.mainOutput
assert(output.Life and output.EnergyShield, 'Engine did not produce defence outputs')
assert(output.Life == player.output.Life and output.EnergyShield == player.output.EnergyShield, 'Main and Calcs defence modes differ; align the Calcs buff mode before auditing the baseline')
local result = {totals = {Life = output.Life, EnergyShield = output.EnergyShield}, attributes = {Str=output.Str, Dex=output.Dex, Int=output.Int}, ledger = {}, breakdown = {}, items = {}, unsupported = {}, diagnostics = logs}
local db = player.modDB
local names = {}
for name in pairs(db.mods) do
 if name:find('Life') or name:find('EnergyShield') or name == 'Defences' or name == 'Str' or name == 'Int' then names[#names + 1] = name end
end
table.sort(names)
for _, name in ipairs(names) do
 for _, kind in ipairs({'BASE', 'INC', 'MORE', 'FLAG', 'OVERRIDE'}) do
  for _, entry in ipairs(db:Tabulate(kind, nil, name)) do
   local mod = entry.mod
   result.ledger[#result.ledger + 1] = {stat = name, kind = kind, value = entry.value, rawValue = mod.value, source = mod.source or 'Unknown', slot = mod.sourceSlot, scope = 'Global'}
  end
 end
end
for _, name in ipairs({'Life', 'EnergyShield', 'Str', 'Int'}) do
 local b = player.breakdown[name] or {}
 local cleaned = {lines = {}, slots = {}}
 for _, line in ipairs(b) do cleaned.lines[#cleaned.lines + 1] = StripEscapes(line) end
 for _, slot in ipairs(b.slots or {}) do
  cleaned.slots[#cleaned.slots + 1] = {source = slot.source, description = slot.sourceName, base = slot.base, increased = slot.inc, more = slot.more, total = slot.total}
 end
 result.breakdown[name] = cleaned
end
for slot, item in pairs(build.calcsTab.mainEnv.player.itemList) do
 if item.armourData then
  result.items[#result.items + 1] = {slot = slot, name = item.name, energyShield = item:GetArmourDataValue('EnergyShield', player.level)}
 end
 for _, field in ipairs({'explicitModLines', 'implicitModLines', 'enchantModLines', 'buffModLines'}) do
  for _, line in ipairs(item[field] or {}) do
   if line.extra and line.extra ~= '' then result.unsupported[#result.unsupported + 1] = {slot=slot, line=line.line, unparsed=line.extra} end
  end
 end
end
-- Missing connector nodes in upstream tree assets are logged at startup. Check
-- allocated node identities separately so a missing allocation cannot pass silently.
local missing = {}
for _, id in ipairs(request.nodes) do
 if not build.spec.tree.nodes[tonumber(id)] then missing[#missing + 1] = id end
end
result.missingAllocatedNodes = missing
for _, slot in ipairs({'Helmet', 'Body Armour', 'Gloves', 'Boots', 'Weapon 2'}) do
 for _, entry in ipairs(db:Tabulate('INC', {slotName=slot}, 'EnergyShield', 'Defences')) do
  local mod = entry.mod
  -- Slot-scoped rows include global modifiers too, making applicability explicit.
  result.ledger[#result.ledger + 1] = {stat=mod.name, kind='INC', value=entry.value, rawValue=mod.value, source=mod.source or 'Unknown', scope=slot}
 end
end
for _, row in ipairs(result.ledger) do
 local id = row.source:match('^Tree:(%d+)')
 local node = id and build.spec.tree.nodes[tonumber(id)]
 if node then row.sourceName = node.name end
end
io.write(json.encode(result))
