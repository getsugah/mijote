import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { test } from 'node:test'
import ts from 'typescript'
import { parse, compileScript } from '@vue/compiler-sfc'
import { createSSRApp } from 'vue'
import { renderToString } from '@vue/server-renderer'

const transpile = text => ts.transpileModule(text,{compilerOptions:{target:ts.ScriptTarget.ES2022,module:ts.ModuleKind.ESNext}}).outputText
const moduleUrl = text => 'data:text/javascript;base64,'+Buffer.from(text).toString('base64')
const apiUrl = moduleUrl(transpile(readFileSync(new URL('../src/api.ts',import.meta.url),'utf8')))
const {photoUrl,uploadPhoto,setCsrf,ApiError} = await import(apiUrl)

test('manual image upload sends binary data with the session CSRF token',async()=>{
  const original=globalThis.fetch;const image=new Blob(['synthetic image bytes'],{type:'image/jpeg'});setCsrf('fictitious-test-token')
  globalThis.fetch=async(path,options)=>{assert.equal(path,'/api/v1/recipes/7/photo');assert.equal(options.body,image);assert.equal(options.headers['X-CSRF-Token'],'fictitious-test-token');assert.equal(options.headers['Content-Type'],'image/jpeg');assert.equal(options.cache,'no-store');return new Response(JSON.stringify({photo_version:'abc'}))}
  try{assert.equal((await uploadPhoto(7,image)).photo_version,'abc')}finally{globalThis.fetch=original;setCsrf('')}
})
test('invalid photos and network failures remain visible errors',async()=>{
  const original=globalThis.fetch
  try{globalThis.fetch=async()=>new Response(JSON.stringify({detail:'Photo illisible'}),{status:422});await assert.rejects(uploadPhoto(1,new Blob()),e=>e instanceof ApiError&&e.status===422);globalThis.fetch=async()=>{throw new Error('offline')};await assert.rejects(uploadPhoto(1,new Blob()),e=>e.status===0)}finally{globalThis.fetch=original}
})
test('photo editor shows the authenticated local image, attribution and explicit save',async()=>{
  const {descriptor}=parse(readFileSync(new URL('../src/RecipePhoto.vue',import.meta.url),'utf8'))
  const script=compileScript(descriptor,{id:'photo-test',inlineTemplate:true})
  const code=transpile(script.content).replace(/from ["']vue["']/g,'from '+JSON.stringify(import.meta.resolve('vue'))).replace(/from ["']\.\/api["']/g,'from '+JSON.stringify(apiUrl))
  const {default:component}=await import(moduleUrl(code))
  const recipe={id:7,name:'Soupe témoin',photo_version:'abc',photo_source:'https://images.example/soupe.jpg',photo_attribution:'Atelier fictif',source_url:'https://recettes.example/soupe'}
  const html=await renderToString(createSSRApp(component,{recipe}))
  assert.match(html,/src="\/api\/v1\/recipes\/7\/photo\?v=abc"/);assert.match(html,/Atelier fictif/)
  assert.match(html,/Conserver cette photo/);assert.match(html,/Retirer la photo/);assert.match(html,/image\/jpeg,image\/png,image\/webp/)
  assert.doesNotMatch(html,/src="https:/);assert.equal(photoUrl(recipe),'/api/v1/recipes/7/photo?v=abc')
})
