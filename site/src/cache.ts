const DB_NAME='sufeelec-public-cache'; const STORE='json';
function open(){return new Promise<IDBDatabase>((resolve,reject)=>{const req=indexedDB.open(DB_NAME,1);req.onupgradeneeded=()=>req.result.createObjectStore(STORE);req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error)})}
export async function cachePut(key:string,value:unknown){try{const db=await open();db.transaction(STORE,'readwrite').objectStore(STORE).put(value,key)}catch{/* optional cache */}}
export async function cacheGet<T>(key:string){try{const db=await open();return await new Promise<T|undefined>((resolve,reject)=>{const req=db.transaction(STORE).objectStore(STORE).get(key);req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error)})}catch{return undefined}}
