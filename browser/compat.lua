-- Lua 5.4 platform/formatting adapters; defence formulae remain upstream.
unpack=table.unpack; loadstring=load; math.pow=function(a,b)return a^b end; math.log10=function(a)return math.log(a,10)end; math.atan2=math.atan
 local originalTostring=tostring
 tostring=function(value)if type(value)=='number' and math.tointeger(value) then return originalTostring(math.tointeger(value))end;return originalTostring(value)end
 local originalLen=string.len
 string.len=function(value)return originalLen(type(value)=='number' and tostring(value) or value)end
 local originalFormat=string.format
 string.format=function(format,...)
  local args=table.pack(...);local index=0
  format=format:gsub('%%[-+ #0]*%d*%.?%d*[cdiouxXeEfgGqs%%aA]',function(spec)
   local kind=spec:sub(-1)
   if kind~='%' then index=index+1
    if kind:match('[diouxX]') and type(args[index])=='number' then
     if args[index]~=args[index] or math.abs(args[index])==math.huge then args[index]='n/a';return '%s' end
     local whole=math.modf(args[index]);args[index]=math.tointeger(whole) or args[index]
    end
   end
   return spec
  end)
  local ok,result=pcall(originalFormat,format,table.unpack(args,1,args.n));if not ok then error(result..';FMT:'..format..';VAL:'..tostring(args[1])..';TYPE:'..tostring(math.type(args[1]))..';MAX:'..math.maxinteger)end;return result
 end
 table.maxn=function(t)local n=0;for k in pairs(t)do if type(k)=='number' and k>n then n=k end end;return n end
 jit={opt={start=function()end}}
 bit={}
 local function signed(n)n=n&0xffffffff;if n>=0x80000000 then return n-0x100000000 end;return n end
 function bit.band(a,...)local v=math.floor(a)&0xffffffff;for _,b in ipairs({...})do v=v&math.floor(b)end;return signed(v)end
 function bit.bor(a,...)local v=math.floor(a)&0xffffffff;for _,b in ipairs({...})do v=v|math.floor(b)end;return signed(v)end
 function bit.bxor(a,...)local v=math.floor(a)&0xffffffff;for _,b in ipairs({...})do v=v~math.floor(b)end;return signed(v)end
 function bit.bnot(a)return signed(~math.floor(a))end
 function bit.lshift(a,b)return signed((math.floor(a)&0xffffffff)<<(b%32))end
 function bit.rshift(a,b)return (math.floor(a)&0xffffffff)>>(b%32)end
 function bit.rol(a,b)b=b%32;a=math.floor(a)&0xffffffff;return signed((a<<b)|(a>>(32-b)))end
 function bit.ror(a,b)return bit.rol(a,32-b)end
 bit.tobit=signed
 package.loaded.bit=bit
 package.preload['lua-utf8']=function()local u={};for k,v in pairs(utf8)do u[k]=v end
 u.gsub=string.gsub;u.find=string.find;u.match=string.match;u.next=utf8.offset
 u.reverse=function(s)local t={};for _,c in utf8.codes(s)do table.insert(t,1,utf8.char(c))end;return table.concat(t)end
 u.sub=function(s,i,j)local n=utf8.len(s);i=i<0 and n+i+1 or i;j=j or n;j=j<0 and n+j+1 or j;return s:sub(utf8.offset(s,i)or (#s+1),(utf8.offset(s,j+1)or (#s+1))-1)end
 return u end
 package.path='../runtime/lua/?.lua;../runtime/lua/?/init.lua;'..package.path
 io.write=function(s)ResultJSON=s end
 arg={'/input.xml','/metadata.json'}
