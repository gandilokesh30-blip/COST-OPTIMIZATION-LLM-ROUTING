const API = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
export async function get(path:string){const r=await fetch(API+path); if(!r.ok) throw new Error(await r.text()); return r.json()}
export async function post(path:string, body:unknown){const r=await fetch(API+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}); if(!r.ok) throw new Error(await r.text()); return r.json()}
export async function patch(path:string, body:unknown){const r=await fetch(API+path,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}); if(!r.ok) throw new Error(await r.text()); return r.json()}
