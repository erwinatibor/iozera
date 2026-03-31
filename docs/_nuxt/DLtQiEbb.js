const e=n=>n.split(`
`).filter(t=>!!t).map(t=>`<span>${t}</span>`).join("")??"",a=n=>n?.replaceAll("{{","<span>").replaceAll("}}","</span>")??"",s=n=>n?.content?.length?n.content.some(t=>t.type==="paragraph"?t.content&&t.content.length>0:!0):!1,r=(n,t="_blank")=>({url:n,linktype:"url",target:t});export{s as a,a as h,e as s,r as t};
