"use strict";(self.webpackChunk=self.webpackChunk||[]).push([[610],{93612:function(mn,nt,f){f.r(nt),f.d(nt,{default:function(){return rn}});var ut=f(5574),M=f.n(ut),Z=f(53343),z=f(91222),dt=f(79928),oe=f(86111),X=null,Ze=!1,de="",Oe="",he=(0,oe.getDvaApp)()._store.dispatch;function ht(o){de=o,X=new dt.Z({getAichatReqParams:function(n){return n}})}function _t(o,t,n){if(!(!X||!de||!o)){var r=o;X.setReconnect(!1),X.createConnect("".concat(r,"?uid=").concat(de)),X.onStatusChange(function(s){var u=s.websocketIsOk;console.log("[ws] status changed:",u),Ze=u,he({type:"chatModel/setChatModel",payload:{isConnect:u}}),u&&(0,z.mf)(t)&&t(),!u&&(0,z.mf)(n)&&n()}),X.onMessage(function(s){console.log("%c [ws] ack message:","color: #07c160; font-size: 14px",s)}),X.onUnknownMethod(function(s){var u=s.type,h=s.data,i=h===void 0?{}:h,p=s.task_id;if(console.log("%c [ws] unKnow ack message:","color: #0ca1f7; font-size: 14px",s),u==="\u601D\u7EEA\u6D41\u6D88\u606F")he({type:"chatModel/setMindStreamList",payload:{message:i}});else if(u==="\u610F\u56FE\u5207\u6362"){var _;he({type:"chatModel/setChatModel",payload:{intention:(_=i.main_task)!==null&&_!==void 0?_:"\u5F53\u524D\u6682\u65E0\u610F\u56FE"}})}else if(u==="\u4EFB\u52A1\u5207\u6362")Oe=p,he({type:"chatModel/fetchGetMissionDetail",payload:{uid:de,method:"get_task_context",seq:"2333",data:{task_id:p}}});else if((i==null?void 0:i.target)==="\u8868\u8FBE\u7BA1\u7406"){var I=(0,oe.getDvaApp)()._store.getState(),y=I.chatModel,x=y===void 0?{}:y,w=x.isMute;he({type:"chatModel/setChatList",payload:{message:{data:i,type:"ai"}}})}else p&&(Oe=p,he({type:"chatModel/fetchGetMissionDetail",payload:{uid:de,method:"get_task_context",seq:"2333",data:{task_id:p}}}))}),X.onError(function(s){console.log("%c [ws] error:","color: #fd9090; font-size: 14px",JSON.stringify(s))})}}function pn(){X.closeConnect()}function at(o){if(!(!X||!Ze)){var t={uid:de,method:"input",data:{content:o},seq:"2333"};X.sendMessage(t),t.type="user",he({type:"chatModel/setChatList",payload:{message:t}})}}function U(){return{isConnected:Ze,chatUid:de,taskId:Oe}}var q=void 0,Ne=!1,ft=function(t){var n=JSON.parse(t.data);if(console.log("[asr] msg",n),n&&n.code===0){var r=n.result,s=r.slice_type,u=r.voice_text_str;s===2&&at(u)}else{var h;console.warn("[asr] \u9519\u8BEF\u6D88\u606F",(h=n==null?void 0:n.message)!==null&&h!==void 0?h:"\u65E0")}};function vt(o){var t=o.onClose,n=o.onError;if(Ne){console.log("[asr] \u8BF7\u52FF\u91CD\u590D\u8FDE\u63A5");return}q=new WebSocket("wss://dev.nekoplan.com/speech-service-atw/v1/wsasr"),q.binaryType="arraybuffer",q.onopen=function(){console.log("[asr] \u8FDE\u63A5\u6210\u529F"),Ne=!0},q.onmessage=ft,q.onerror=function(r){console.warn("[asr] \u8FDE\u63A5\u9519\u8BEF"),Ne=!1,(0,z.mf)(n)&&n(r)},q.onclose=function(){console.warn("[asr] \u8FDE\u63A5\u5173\u95ED"),Ne=!1,(0,z.mf)(t)&&t()}}function it(){q&&Ne&&(q.close(),q=void 0)}function mt(o){q&&q.send(o)}var yn=f(15009),gn=f(99289),pt=f(19632),st=f.n(pt),yt=f(72004),gt=f.n(yt),xt=f(12444),jt=f.n(xt),St=f(9783),$=f.n(St),bt=gt()(function o(){jt()(this,o),$()(this,"items",[]),$()(this,"enqueue",function(t){this.items.push(t)}),$()(this,"dequeue",function(){return this.items.shift()}),$()(this,"splice",function(t){items=[].concat(st()(this.items),st()(t))}),$()(this,"sort",function(t){this.items.sort(function(n,r){return n[t]-r[t]})}),$()(this,"checkFront",function(t,n){return this.items.slice(t,n)}),$()(this,"front",function(){return this.items[0]}),$()(this,"isEmpty",function(){return this.items.length===0}),$()(this,"clear",function(){this.items=[]}),$()(this,"size",function(){return this.items.length}),$()(this,"print",function(){console.log(this.items.toString())})}),we=null,We=!1,ct=0,Ue=null,_e=new bt;function Mt(){we=new AudioContext({latencyHint:"balanced"})}function Be(o){var t=ct;ct++,fetchTTS({text:o}).then(function(){var n=_asyncToGenerator(_regeneratorRuntime().mark(function r(s){var u;return _regeneratorRuntime().wrap(function(i){for(;;)switch(i.prev=i.next){case 0:if(!(s&&s.status===200)){i.next=13;break}return i.prev=1,i.next=4,s.arrayBuffer();case 4:u=i.sent,Te({arraybuffer:u,index:t}),i.next=11;break;case 8:i.prev=8,i.t0=i.catch(1),console.warn("tts\u89E3\u6790\u9519\u8BEF",i.t0);case 11:i.next=14;break;case 13:Te({arraybuffer:null,index:t});case 14:case"end":return i.stop()}},r,null,[[1,8]])}));return function(r){return n.apply(this,arguments)}}()).catch(function(n){Te({arraybuffer:null,index:t})})}function Te(o){return He.apply(this,arguments)}function He(){return He=_asyncToGenerator(_regeneratorRuntime().mark(function o(t){var n,r,s,u,h,i;return _regeneratorRuntime().wrap(function(_){for(;;)switch(_.prev=_.next){case 0:if(n=t.arraybuffer,r=t.index,s=function(){if(!_e.isEmpty()){var y=_e.dequeue();Te(y)}},!(!we||!isArrayBuffer(n))){_.next=6;break}return Ue=r,s(),_.abrupt("return");case 6:if(!We){_.next=10;break}_e.enqueue({arraybuffer:n,index:r}),_.next=27;break;case 10:if(r===Ue+1){_.next=17;break}_e.enqueue({arraybuffer:n,index:r}),_e.sort("index"),u=_e.dequeue(),u.index===Ue+1?Te(u):_e.enqueue(u),_.next=27;break;case 17:return _.next=19,we.decodeAudioData(n);case 19:h=_.sent,i=we.createBufferSource(),i.buffer=h,i.connect(we.destination),i.onended=function(){We=!1,s()},i.start(0),We=!0,Ue=r;case 27:case"end":return _.stop()}},o)})),He.apply(this,arguments)}function xn(){}function jn(){Be("\u8FD9\u662F\u7B2C\u4E00\u53E5"),Be("\u4F60\u597D\uFF0C\u8FD9\u662F\u7B2C\u4E8C\u53E5,\u522B\u8D70\u5F00\u54E6"),Be("\u518D\u89C1")}var Ct=f(57584),Ge=f.n(Ct),Sn=f(10884),bn=f(27538),le=null,Ke=null;function kt(o){var t=o!=null?o:{},n=t.type,r=n===void 0?"pcm":n,s=t.bitRate,u=s===void 0?16:s,h=t.sampleRate,i=h===void 0?16e3:h,p=t.process,_=p===void 0?function(){}:p,I=function(x,w,P,D){Ke&&Ke.input(x[x.length-1],w,D),(0,z.mf)(_)&&_(Ge().SampleData(x.slice(-1),D,i).data)};le=new(Ge())({type:r,bitRate:u,sampleRate:i,onProcess:I})}function Nt(o){Ke=Ge().WaveView(o)}function wt(o){if(!le){console.log("\u83B7\u53D6\u5F55\u97F3\u6743\u9650\u5931\u8D25\uFF0C\u672A\u521D\u59CB\u5316");return}var t=o!=null?o:{},n=t.success,r=n===void 0?function(){}:n,s=t.fail,u=s===void 0?function(){}:s,h=function(_){console.log("[Recorder H5] open success"),(0,z.mf)(r)&&r(_)},i=function(_){console.log("[Recorder H5] open fail"),(0,z.mf)(u)&&u(_)};le.open(h,i)}function Mn(o){if(le){var t=o!=null?o:{},n=t.success,r=n===void 0?function(){}:n,s=function(h){console.log("[Recorder H5] close success"),isFunction(r)&&r(h)};le.close(s)}}function Tt(){le.start()}function At(o){if(le){var t=o!=null?o:{},n=t.success,r=n===void 0?function(){}:n,s=t.fail,u=s===void 0?function(){}:s,h=function(_){(0,z.mf)(r)&&r(_)},i=function(_){(0,z.mf)(u)&&u(_)};le.stop(h,i,!1)}}var It=f(35102),Dt=f(71965),Re=f(68872),Ae=f(41202),Ie=f(23324),se=f(14726),Ve=f(47153),Je=f(96486),Et=f(20091),m=f(67294),l={link:"link___VCmRN",link__input:"link__input___Lc8in",link__btn:"link__btn___a3gJz",point:"point___naUO2",point_inside:"point_inside___hsc3O",link_inside:"link_inside___J0xaj",disLink:"disLink___Olkku",disLink_inside:"disLink_inside___x1H34",mobile:"mobile___sy4aC",mobile2:"mobile2___Am0Tt",mobile3:"mobile3___Tqdbi",chat:"chat___YRMf0",chat__top:"chat__top___p2PQ6",chat__top__btn:"chat__top__btn___hE3u5",chat__top__btn_margin:"chat__top__btn_margin___nIF68",chat__top__btn_voice:"chat__top__btn_voice___Gq6ST",voiceOn:"voiceOn___M20h8",voiceOff:"voiceOff___MKs98",chat__intention:"chat__intention___cKdZ0",chat__intention_title:"chat__intention_title___rbz93",chat__intention_text:"chat__intention_text___yDB5D",chat__content:"chat__content___vd_jq",user:"user___p1tXs",ai:"ai___vXkbg",item:"item___Iey9r",item__icon_user:"item__icon_user___kXxLe",item__icon_ai:"item__icon_ai___aMdQ3",item__text:"item__text___G616U",item__text_time:"item__text_time___pf1vX",right:"right___Xf3f6",item__text_content:"item__text_content___mKBVx",chat__content_line:"chat__content_line___PzX1s",chat__input:"chat__input___fLbky",chat__input_area:"chat__input_area___NdxTQ",chat__input_btn:"chat__input_btn___ypUAL",chat__input_switch:"chat__input_switch___KT4Be",cube:"cube___PCVMV",talk:"talk___RIB1U",chat__input_micro:"chat__input_micro___RrHGy"},e=f(85893),Ut={elem:".recorderWave",width:500,height:30,keep:!1,lineWidth:2,scale:1,phase:21.8},Rt=function(t){var n=t.chatModel,r=t.dispatch,s=n.chatList,u=n.historyChatList,h=n.isConnect,i=n.intention,p=n.isMute,_=Re.ZP.useMessage(),I=M()(_,2),y=I[0],x=I[1],w=(0,m.useState)(!0),P=M()(w,2),D=P[0],k=P[1],G=(0,m.useState)(""),F=M()(G,2),E=F[0],W=F[1],ce=(0,m.useState)("ws://localhost/mts_agent/dialogue/v1/dialogue"),B=M()(ce,2),R=B[0],ne=B[1],ae=(0,m.useState)(""),K=M()(ae,2),N=K[0],ie=K[1],xe=(0,m.useState)(!1),je=M()(xe,2),Se=je[0],Fe=je[1],be=(0,m.useState)(!1),Me=M()(be,2),V=Me[0],ye=Me[1],ue=(0,m.useRef)(),Ce=new Et.Z({html:!1,linkify:!0,typographer:!1});(0,m.useEffect)(function(){kt({process:function(a){mt(a.buffer)}}),Mt()},[]),(0,m.useEffect)(function(){localStorage.setItem("MTS_TOOL_AUDIO_STATE",p?"true":"false")},[p]),(0,m.useEffect)(function(){ue.current&&(ue.current.scrollTop=ue.current.scrollHeight)},[s,u]),(0,m.useEffect)(function(){V?(vt({onClose:function(){ye(!1)},onError:function(a){console.warn("[asr] \u8FDE\u63A5\u610F\u5916\u65AD\u5F00",a),y.error("ASR\u8FDE\u63A5\u5DF2\u65AD\u5F00")}}),Nt(Ut),wt({success:function(){console.log("\u9EA6\u514B\u98CE\u6743\u9650\u83B7\u53D6\u6210\u529F\uFF0Copen"),Tt()},fail:function(a){y.error(a!=null?a:"\u83B7\u53D6\u9EA6\u514B\u98CE\u6743\u9650\u5931\u8D25"),it(),ye(!1)}})):(it(),At())},[V]);var De=function(){if(!E){y.warning("\u8BF7\u8F93\u5165uid");return}if(!R){y.warning("\u8BF7\u8F93\u5165url");return}var a=function(){y.success("\u8FDE\u63A5\u6210\u529F"),j(),c(),d(),g()},T=function(){y.error("\u8FDE\u63A5\u65AD\u5F00")};ht(E),_t(R,a,T)},ke=function(){if(!h){y.warning("\u5F53\u524Dwebsocket\u79BB\u7EBF\uFF0C\u8BF7\u5148\u521B\u5EFA\u8FDE\u63A5");return}if(!N||!N.trim()){ie("");return}at(N),ie("")},Ee=(0,Je.debounce)(function(b){var a=b.target.value?"\u7EFF\u706F":"\u7EA2\u706F",T=U(),L=T.chatUid;(0,Z.HD)({uid:L,method:"set_exp_status",seq:"2333",data:{status:a}}).then(function(H){if(H&&H.success)y.success("\u5207\u6362\u6210\u529F"),k(b.target.value),r({type:"chatModel/setChatList",payload:{message:{type:"line",content:"\u5DF2\u5207\u6362\u4E3A".concat(a)}}});else{var te;y.error((te=H==null?void 0:H.msg)!==null&&te!==void 0?te:"\u5207\u6362\u5931\u8D25")}})},1e3),j=function(){var a=U(),T=a.chatUid;(0,Z.HD)({uid:T,method:"get_exp_status",seq:"2333"}).then(function(L){if(L&&L.success){var H=L.data.status;k(H==="\u7EFF\u706F")}})},c=function(){var a=U(),T=a.chatUid;r({type:"chatModel/fetchGetHistoryChat",payload:{uid:T,method:"get_history_dialog",seq:"2333"}})},d=function(){var a=U(),T=a.chatUid;r({type:"chatModel/fetchGetRole",payload:{uid:T,method:"get_robot_role",seq:"2333"}})},g=function(){var a=U(),T=a.chatUid;r({type:"chatModel/fetchGetIntention",payload:{uid:T,method:"get_intention",seq:"2333",data:{}}})},C=function(){var a=U(),T=a.chatUid;if(!h){y.warning("\u5F53\u524Dwebsocket\u79BB\u7EBF\uFF0C\u8BF7\u5148\u521B\u5EFA\u8FDE\u63A5");return}Ae.Z.confirm({title:"\u63D0\u793A",content:"\u662F\u5426\u6E05\u9664\u5BF9\u8BDD\u8BB0\u5F55",cancelText:"\u53D6\u6D88",okText:"\u6E05\u9664",onOk:(0,Je.debounce)(function(){(0,Z.gM)({uid:T,method:"clear_dialogue_history",seq:"2333"}).then(function(L){var H=L.success;if(H)y.success("\u6E05\u9664\u5BF9\u8BDD\u6210\u529F"),r({type:"chatModel/setChatList",payload:{message:{type:"line",content:"\u4EE5\u4E0A\u5BF9\u8BDD\u5DF2\u6E05\u9664"}}});else{var te;y.error((te=L==null?void 0:L.msg)!==null&&te!==void 0?te:"\u6E05\u9664\u5931\u8D25")}})},500)})},S=(0,Je.debounce)(function(){if(!h){y.warning("\u5F53\u524Dwebsocket\u79BB\u7EBF\uFF0C\u8BF7\u5148\u521B\u5EFA\u8FDE\u63A5");return}var b=U(),a=b.chatUid;(0,Z.HD)({uid:a,method:"clear_robot_role",seq:"2333"}).then(function(T){var L=T.success;if(L)y.success("\u6E05\u9664\u89D2\u8272\u6210\u529F"),r({type:"chatModel/setChatList",payload:{message:{type:"line",content:"\u5F53\u524D\u89D2\u8272\u5DF2\u91CD\u7F6E"}}}),r({type:"chatModel/setChatModel",payload:{globalRole:""}});else{var H;y.error((H=T==null?void 0:T.msg)!==null&&H!==void 0?H:"\u6E05\u9664\u5931\u8D25")}})},500),v=function(){},A=function(){if(!h){y.warning("\u5F53\u524Dwebsocket\u79BB\u7EBF\uFF0C\u8BF7\u5148\u521B\u5EFA\u8FDE\u63A5");return}V||ye(!0)},J=function(){r({type:"chatModel/setChatModel",payload:{isMute:!p}})},un=function(a,T){var L=a.role;return L==="user"?(0,e.jsxs)("div",{className:"".concat(l.item," ").concat(l.user),children:[(0,e.jsxs)("div",{className:l.item__text,children:[(0,e.jsx)("div",{className:"".concat(l.item__text_time," ").concat(l.right),children:"--"}),(0,e.jsx)("div",{className:l.item__text_content,children:a==null?void 0:a.content})]}),(0,e.jsx)("div",{className:l.item__icon_user})]},T):(0,e.jsxs)("div",{className:"".concat(l.item," ").concat(l.ai),children:[(0,e.jsx)("div",{className:l.item__icon_ai}),(0,e.jsxs)("div",{className:l.item__text,children:[(0,e.jsx)("div",{className:l.item__text_time,children:"--"}),(0,e.jsx)("div",{className:l.item__text_content,dangerouslySetInnerHTML:{__html:Ce.renderInline((0,z.HD)(a==null?void 0:a.content)?a==null?void 0:a.content:" ")}})]})]},T)},dn=function(a,T){var L=a.type,H=a.currentRole;if(L==="user"){var te,qe;return(0,e.jsxs)("div",{className:"".concat(l.item," ").concat(l.user),children:[(0,e.jsxs)("div",{className:l.item__text,children:[(0,e.jsx)("div",{className:"".concat(l.item__text_time," ").concat(l.right),children:(te=a==null?void 0:a.time)!==null&&te!==void 0?te:""}),(0,e.jsx)("div",{className:l.item__text_content,children:a==null||(qe=a.data)===null||qe===void 0?void 0:qe.content})]}),(0,e.jsx)("div",{className:l.item__icon_user})]},T)}if(L==="ai"){var $e,et,tt;return(0,e.jsxs)("div",{className:"".concat(l.item," ").concat(l.ai),children:[(0,e.jsx)("div",{className:l.item__icon_ai}),(0,e.jsxs)("div",{className:l.item__text,children:[(0,e.jsxs)("div",{className:l.item__text_time,children:[(0,e.jsx)("span",{children:H?"<".concat(H,">"):""}),($e=a==null?void 0:a.time)!==null&&$e!==void 0?$e:""]}),(0,e.jsx)("div",{className:l.item__text_content,dangerouslySetInnerHTML:{__html:Ce.renderInline((0,z.HD)(a==null||(et=a.data)===null||et===void 0?void 0:et.content)?a==null||(tt=a.data)===null||tt===void 0?void 0:tt.content:" ")}})]})]},T)}if(L==="line"&&a.content)return(0,e.jsx)("div",{className:l.chat__content_line,children:a.content})},hn=function(){return(0,e.jsx)("div",{className:l.chat__content_line,children:"----------------\u4EE5\u4E0A\u4E3A\u5386\u53F2\u5BF9\u8BDD----------------"})},_n=(0,e.jsx)("div",{className:"".concat(l.point," ").concat(h?l.link:l.disLink),children:(0,e.jsx)("div",{className:"".concat(l.point_inside," ").concat(h?l.link_inside:l.disLink_inside)})}),fn=function(){return(0,e.jsxs)(m.Fragment,{children:[(0,e.jsx)("div",{className:l.chat__input_switch,onClick:v,children:(0,e.jsx)(It.Z,{})}),(0,e.jsx)(Ie.Z,{className:l.chat__input_area,placeholder:"\u8BF7\u8F93\u5165\u5BF9\u8BDD\u5185\u5BB9",value:N,onChange:function(T){ie(T.target.value)},onPressEnter:ke}),(0,e.jsx)(se.ZP,{className:l.chat__input_btn,type:"primary",onClick:ke,children:"\u53D1\u9001"})]})},vn=function(){return(0,e.jsxs)(m.Fragment,{children:[(0,e.jsx)("div",{className:"".concat(l.chat__input_switch," ").concat(V?l.talk:""),onClick:v,children:V?(0,e.jsx)("div",{className:l.cube}):(0,e.jsx)(Dt.Z,{})}),(0,e.jsx)("div",{className:l.chat__input_micro,onClick:A,children:V?(0,e.jsx)("div",{class:"recorderWave",style:{width:"540px",height:"30px"}}):"\u5F00\u59CB\u8BF4\u8BDD"})]})};return(0,e.jsxs)(m.Fragment,{children:[(0,e.jsxs)("div",{className:l.link,children:[(0,e.jsx)(Ie.Z,{placeholder:"\u8BF7\u8F93\u5165uid",className:"".concat(l.link__input," ").concat(l.mobile),value:E,onChange:function(a){W(a.target.value)}}),(0,e.jsx)(Ie.Z,{placeholder:"\u8BF7\u8F93\u5165url",className:"".concat(l.link__input," ").concat(l.mobile2),value:R,onChange:function(a){ne(a.target.value)}}),(0,e.jsx)(se.ZP,{type:"primary",icon:_n,ghost:!0,className:"".concat(l.link__btn," ").concat(l.mobile3),onClick:De,children:h?"\u5DF2\u8FDE\u63A5":"\u8FDE\u63A5"})]}),(0,e.jsxs)("div",{className:l.chat,children:[(0,e.jsxs)("div",{className:l.chat__top,children:[(0,e.jsxs)("div",{className:l.chat__top__btn,children:[(0,e.jsx)(se.ZP,{type:"primary",ghost:!0,onClick:C,children:"\u6E05\u9664\u5BF9\u8BDD\u8BB0\u5F55"}),(0,e.jsx)(se.ZP,{type:"primary",className:l.chat__top__btn_margin,ghost:!0,onClick:S,children:"\u6E05\u9664\u5F53\u524D\u89D2\u8272"})]}),(0,e.jsxs)(Ve.ZP.Group,{value:D,onChange:Ee,disabled:!h,children:[(0,e.jsx)(Ve.ZP,{value:!1,children:"\u7EA2\u706F"}),(0,e.jsx)(Ve.ZP,{value:!0,children:"\u7EFF\u706F"})]})]}),h&&(0,e.jsxs)("div",{className:l.chat__intention,children:[(0,e.jsx)("div",{className:l.chat__intention_title,children:"\u610F\u56FE\uFF1A"}),(0,e.jsx)("div",{className:l.chat__intention_text,children:i})]}),(0,e.jsxs)("div",{className:l.chat__content,ref:ue,children:[u.map(function(b,a){return un(b,a)}),u.length>0&&hn(),s.map(function(b,a){return dn(b,a)})]}),(0,e.jsx)("div",{className:l.chat__input,children:Se?vn():fn()})]}),x]})},Lt=(0,oe.connect)(function(o){var t=o.chatModel;return{chatModel:t}})(Rt),Pt=f(72269),ot=f(57135),Ft=f(27484),Ye=f.n(Ft),ee={wrapper:"wrapper___nnTjx",empty:"empty___VfKKj",mind:"mind___RiYB7",item:"item___H_SFj",item_key:"item_key___Y0BwJ",item_value:"item_value___Y0aZ5",enhance:"enhance___AtFB2",time:"time___Fu0nd"},Zt=["content","source","target","response","attention","msg"],Ot=["response","msg","content"],Wt=function(t){var n=t.chatModel,r=t.isSimplify,s=r===void 0?!1:r,u=n.mindStream;(0,m.useEffect)(function(){},[u]);var h=(0,e.jsx)("div",{className:ee.empty,children:"\u6682\u65E0\u601D\u7EEA\u6D41"}),i=function(_,I){var y=function(k){var G=null;k.time?(G=k.time,delete k.time):G=Ye()().format("HH:mm:ss");var F=Object.entries(k);return s&&(F=F.filter(function(E){var W=M()(E,2),ce=W[0],B=W[1];return Zt.includes(ce)})),{time:G,resList:F}},x=y(JSON.parse(JSON.stringify(_))),w=x.time,P=x.resList;return(0,e.jsxs)("div",{className:ee.mind,children:[(0,e.jsxs)("div",{className:"".concat(ee.item," ").concat(ee.time),children:[(0,e.jsx)("div",{className:ee.item_key,children:"\u65F6\u95F4"}),(0,e.jsx)("div",{className:ee.item_value,children:w!=null?w:"--"})]}),P.map(function(D,k){return(0,e.jsxs)("div",{className:ee.item,children:[(0,e.jsx)("div",{className:ee.item_key,children:"".concat(D[0],":")}),(0,e.jsx)("div",{className:"".concat(ee.item_value," ").concat(Ot.includes(D[0])?ee.enhance:""),children:JSON.stringify(D[1])})]},k)})]},I)};return(0,e.jsx)("div",{className:ee.wrapper,children:u.length>0?u.map(function(p,_){return i(p,_)}):h})},Bt=(0,oe.connect)(function(o){var t=o.chatModel;return{chatModel:t}})(Wt),Qe=f(2096),Ht=f(55171),ze=f.n(Ht),fe={wrapper:"wrapper___q8ufk",empty:"empty___ltA1p",detail:"detail___MD_ag",detail__id:"detail__id___HjaLl",detail__id_title:"detail__id_title___dcYTg",detail__id_num:"detail__id_num___KbyHe",detail__json:"detail__json___ANb4P"},Gt=function(t){var n=t.chatModel,r=t.visible,s=t.dispatch,u=n.missionDetail,h=n.missionId,i=(0,m.useState)(!1),p=M()(i,2),_=p[0],I=p[1],y=Re.ZP.useMessage(),x=M()(y,2),w=x[0],P=x[1];(0,m.useEffect)(function(){if(r){var F=U(),E=F.chatUid,W=F.taskId;E&&W&&s({type:"chatModel/fetchGetMissionDetail",payload:{uid:E,method:"get_task_context",seq:"2333",data:{task_id:W}}})}},[r]),(0,m.useEffect)(function(){u&&Object.keys(u).length>0?I(!0):I(!1)},[u]);var D=function(){try{if(navigator.clipboard)navigator.clipboard.writeText(h).then(function(){w.success("\u590D\u5236\u6210\u529F")});else{var E=document.createElement("textarea");document.body.appendChild(E),E.value=h,E.select(),document.execCommand("copy")&&(document.execCommand("copy"),w.success("\u590D\u5236\u6210\u529F")),document.body.removeChild(E)}}catch(W){w.error("\u5F53\u524D\u6D4F\u89C8\u5668\u4E0D\u652F\u6301\u590D\u5236\uFF0C\u8BF7\u624B\u52A8\u590D\u5236")}},k=(0,e.jsx)("div",{className:fe.empty,children:"\u6682\u65E0\u4EFB\u52A1\u4FE1\u606F"}),G=function(){return(0,e.jsxs)("div",{className:fe.detail,children:[h?(0,e.jsxs)("div",{className:fe.detail__id,children:[(0,e.jsx)("div",{className:fe.detail__id_title,children:"task_id:"}),(0,e.jsx)(Qe.Z,{title:"\u70B9\u51FB\u590D\u5236",children:(0,e.jsx)("div",{className:fe.detail__id_num,onClick:D,children:h})})]}):null,(0,e.jsx)("div",{className:fe.detail__json,children:(0,e.jsx)(ze(),{src:u,name:"\u5F53\u524D\u4EFB\u52A1\u4FE1\u606F",collapsed:1,displayDataTypes:!1})}),P]})};return(0,e.jsx)("div",{className:fe.wrapper,children:_?G():k})},Kt=(0,oe.connect)(function(o){var t=o.chatModel;return{chatModel:t}})(Gt),Xe={wrapper:"wrapper___jTwi3",empty:"empty___rbKTQ",detail:"detail___ep9gi"},Vt=function(t){var n=t.chatModel,r=t.visible,s=t.dispatch,u=n.workMemory,h=(0,m.useState)(!1),i=M()(h,2),p=i[0],_=i[1];(0,m.useEffect)(function(){r&&I()},[r]),(0,m.useEffect)(function(){u&&Object.keys(u).length>0?_(!0):_(!1)},[u]);var I=function(){var P=U(),D=P.isConnected,k=P.chatUid;D&&k&&s({type:"chatModel/fetchGetWorkMemory",payload:{uid:k,method:"get_work_memory",seq:"2333"}})},y=(0,e.jsx)("div",{className:Xe.empty,children:"\u6682\u65E0\u5DE5\u4F5C\u8BB0\u5FC6"}),x=function(){return(0,e.jsx)("div",{className:Xe.detail,children:(0,e.jsx)(ze(),{src:u,name:"\u5DE5\u4F5C\u8BB0\u5FC6",collapsed:1,displayDataTypes:!1})})};return(0,e.jsx)("div",{className:Xe.wrapper,children:p?x():y})},Jt=(0,oe.connect)(function(o){var t=o.chatModel;return{chatModel:t}})(Vt),ge={display:"display___X86X8",tab:"tab___AOdT_",switch:"switch___A2Y3L",stone:"stone___xTzlF"},re=["mind","mission","memory"];function Yt(){var o=(0,m.useState)(re[0]),t=M()(o,2),n=t[0],r=t[1],s=(0,m.useState)(!1),u=M()(s,2),h=u[0],i=u[1],p=[{key:re[0],label:"\u601D\u7EEA\u6D41",children:(0,e.jsx)("div",{className:ge.tab,children:(0,e.jsx)(Bt,{isSimplify:h})})},{key:re[1],label:"\u5F53\u524D\u4EFB\u52A1\u4FE1\u606F",children:(0,e.jsx)("div",{className:ge.tab,children:(0,e.jsx)(Kt,{visible:n===re[1]})})},{key:re[2],label:"\u5DE5\u4F5C\u8BB0\u5FC6",children:(0,e.jsx)("div",{className:ge.tab,children:(0,e.jsx)(Jt,{visible:n===re[2]})})}],_=function(w){r(w)},I=(0,e.jsx)("div",{className:ge.stone}),y=(0,m.useMemo)(function(){var x=function(P){i(P)};return n===re[0]?(0,e.jsx)(Pt.Z,{className:ge.switch,value:h,checkedChildren:"\u7CBE\u7B80",unCheckedChildren:"\u666E\u901A",onChange:x}):I},[n,h]);return(0,e.jsx)("div",{className:ge.display,children:(0,e.jsx)(ot.Z,{defaultActiveKey:re[0],onChange:_,tabBarExtraContent:{left:y,right:I},centered:!0,items:p})})}var Qt=f(97857),Le=f.n(Qt),zt=f(97937),Xt=f(88484),qt=f(98165),$t=f(55854),Q={wrapper:"wrapper___wyzU9",upload:"upload___FMzEk",count:"count___dOpvt",count_text:"count_text___RrfRr",count_icon:"count_icon____mUFi",content:"content___KW54p",list:"list___erTI_",file:"file___KmD01",file_name:"file_name___lWJ7X",file_status:"file_status___YXUJv",file_time:"file_time___GX9rB",file_btn:"file_btn___cMoJr"},lt=void 0,Pe=null,en=function(t){var n=t.visible,r=t.chatModel,s=r.isConnect,u=(0,m.useRef)(),h=Re.ZP.useMessage(),i=M()(h,2),p=i[0],_=i[1],I=(0,m.useState)([]),y=M()(I,2),x=y[0],w=y[1],P=(0,m.useState)([]),D=M()(P,2),k=D[0],G=D[1],F=(0,m.useState)(0),E=M()(F,2),W=E[0],ce=E[1],B=(0,m.useState)(!1),R=M()(B,2),ne=R[0],ae=R[1],K=(0,m.useState)([]),N=M()(K,2),ie=N[0],xe=N[1],je=(0,m.useState)(!1),Se=M()(je,2),Fe=Se[0],be=Se[1],Me=function(){var j;return function(c,d){return j||(j=c,d&&d(c)),{fileList:j,reset:function(){j=!1}}}}();(0,m.useEffect)(function(){return n&&(V(),Pe=setInterval(function(){V()},10*1e3)),function(){Pe&&(clearInterval(Pe),Pe=null)}},[n]),(0,m.useEffect)(function(){if(k.length>0){var j=U(),c=j.chatUid,d=new FormData;k.forEach(function(g){d.append("upload_files",g)}),d.append("confidence",50),d.append("uid",c),(0,Z.Ki)(d).then(function(g){if(g&&g.success){var C=g.data,S=Object.values(C),v=S.filter(function(A){return A.err!==""});console.log("\u9519\u8BEF\u4FE1\u606F",v),v.length>0?(xe(v),be(!0)):p.success("\u4E0A\u4F20\u6210\u529F"),V()}else p.error("\u4E0A\u4F20\u5931\u8D25")}),u.current.reset(),G([])}},[k]);var V=function(c){var d=U(),g=d.chatUid,C=d.isConnected;g&&C&&(0,Z.gf)({cursor:0,limit:100,uid:g}).then(function(S){if(S&&S.success){var v=S.data,A=v.total,J=v.infos;w(J),ce(A),c&&c(S)}})},ye=function(c){c&&c.success?p.success("\u5237\u65B0\u6210\u529F"):p.error("\u5237\u65B0\u5931\u8D25")},ue=function(c){(0,Z.cy)({ids:[c]}).then(function(d){d&&d.success?(p.success("\u5220\u9664\u6210\u529F"),V()):p.error("\u5220\u9664\u5931\u8D25")})},Ce=function(c,d){var g,C={0:"\u5F85\u5904\u7406",1:"\u5904\u7406\u4E2D",2:"\u6210\u529F",3:"\u5931\u8D25"},S={0:"#000000",1:"#2c6fff",2:"#1d8b1d",3:"#ff2b2b"};return(0,e.jsxs)("div",{className:Q.file,children:[(0,e.jsx)("div",{className:Q.file_name,children:(0,e.jsx)(Qe.Z,{title:c.name,children:c.name})}),(0,e.jsx)("div",{className:Q.file_status,style:{color:S[c.status]},children:C[c.status]}),(0,e.jsx)("div",{className:Q.file_time,children:Ye().unix(c.gmt_create).format("YYYY/M/D")}),(0,e.jsx)("div",{className:Q.file_btn,onClick:ue.bind(lt,c.id),children:(0,e.jsx)(zt.Z,{})})]},(g=c.id)!==null&&g!==void 0?g:d)},De=(0,m.useMemo)(function(){return(0,e.jsx)("ul",{children:ie.map(function(j,c){return(0,e.jsx)("li",{children:j.err},c)})})},[ie]),ke={accept:".doc,.docx",showUploadList:!1,multiple:!0,beforeUpload:function(c,d){return u.current=Me(d,G),!1}},Ee={title:"\u4E0A\u4F20\u5F02\u5E38",open:Fe,closeIcon:!1,okText:"\u786E\u5B9A",cancelButtonProps:{style:{display:"none"}},onOk:function(){xe([]),be(!1)}};return(0,e.jsxs)("div",{className:Q.wrapper,children:[(0,e.jsxs)("div",{className:Q.upload,children:[(0,e.jsx)($t.Z,Le()(Le()({},ke),{},{children:(0,e.jsx)(Qe.Z,{title:"\u76EE\u524D\u4EC5\u652F\u6301\u4E2D\u6587\u6587\u6863\uFF0C\u53EF\u6309\u4F4Fctrl\u591A\u9009",children:(0,e.jsx)(se.ZP,{disabled:!s,icon:(0,e.jsx)(Xt.Z,{}),children:"\u70B9\u51FB\u4E0A\u4F20\u6587\u4EF6"})})})),(0,e.jsxs)("div",{className:Q.count,children:[(0,e.jsx)("div",{className:Q.count_text,children:"\u603B\u6570:".concat(W)}),(0,e.jsx)("div",{className:Q.count_icon,onMouseEnter:function(){ae(!0)},onMouseLeave:function(){ae(!1)},onClick:V.bind(lt,ye),title:"\u5237\u65B0",children:(0,e.jsx)(qt.Z,{spin:ne})})]})]}),(0,e.jsx)("div",{className:Q.content,children:(0,e.jsx)("div",{className:Q.list,children:x.map(function(j){return Ce(j)})})}),(0,e.jsx)(Ae.Z,Le()(Le()({},Ee),{},{children:De})),_]})},tn=(0,oe.connect)(function(o){var t=o.chatModel;return{chatModel:t}})(en),nn=f(42192),Y={wrapper:"wrapper___lgB8c",detail:"detail___W5mat",detail__json:"detail__json___TNOfM",empty:"empty___ggOD8",input:"input___iBJjV",input_text:"input_text___DE9Rl",input_btn:"input_btn___pKojm",memory:"memory___MwtRi",memory_total:"memory_total___HIyQ0",memory__item:"memory__item___KnNjw",memory__item_content:"memory__item_content___wrG8T",memory__item_red:"memory__item_red___inZ4_",memory__item_blue:"memory__item_blue___ubbtW"},rt=[{value:"\u731C\u60F3",label:"\u731C\u60F3"},{value:"\u7528\u6237\u9648\u8FF0",label:"\u7528\u6237\u9648\u8FF0"},{value:"\u7ED3\u8BBA",label:"\u7ED3\u8BBA"}],an=function(t){var n=t.visible,r=t.action,s=t.name,u=t.search,h=u===void 0?!1:u,i=t.isMemory,p=i===void 0?!1:i,_=t.tips,I=(0,m.useState)(null),y=M()(I,2),x=y[0],w=y[1],P=(0,m.useState)(p?rt[0].value:""),D=M()(P,2),k=D[0],G=D[1];(0,m.useEffect)(function(){n&&r&&!h&&r().then(function(B){B&&Object.keys(B).length>0?w(B):w(null)})},[n]);var F=(0,e.jsx)("div",{className:Y.empty,children:"\u6682\u65E0".concat(s)}),E=function(){var R=function(N){var ie=N.target.value;G(ie)},ne=function(N){G(N)},ae=function(){r(k).then(function(N){N&&Object.keys(N).length>0?w(N):w(null)})};return(0,e.jsxs)("div",{className:Y.input,children:[p?(0,e.jsx)(nn.Z,{className:Y.input_text,options:rt,value:k,onChange:ne,placeholder:_!=null?_:"\u8BF7\u9009\u62E9\u68C0\u7D22\u6761\u4EF6"}):(0,e.jsx)(Ie.Z,{className:Y.input_text,value:k,onChange:R,placeholder:_!=null?_:"\u8BF7\u8F93\u5165\u68C0\u7D22\u6761\u4EF6"}),(0,e.jsx)(se.ZP,{className:Y.input_btn,type:"primary",onClick:ae,children:"\u67E5\u8BE2"})]})},W=(0,m.useMemo)(function(){return(0,e.jsx)("div",{className:Y.detail__json,children:(0,e.jsx)(ze(),{src:x,name:s,collapsed:1,displayDataTypes:!1})})},[x,s]),ce=(0,m.useMemo)(function(){if(!x)return null;var B=x.total,R=B===void 0?0:B,ne=x.infos,ae=ne===void 0?[]:ne;return(0,e.jsxs)("div",{className:Y.memory,children:[(0,e.jsxs)("div",{className:Y.memory_total,children:["\u603B\u6570\uFF1A",R]}),(0,e.jsx)("div",{children:ae.map(function(K){return(0,e.jsxs)("div",{className:Y.memory__item,children:[(0,e.jsx)("div",{children:Ye()(K.timestamp).format("YYYY-MM-DD HH:mm:ss")}),(0,e.jsx)("div",{className:Y.memory__item_content,children:K.content}),(0,e.jsxs)("div",{children:[(0,e.jsx)("span",{className:Y.memory__item_red,children:"attention: "}),(0,e.jsx)("span",{className:Y.memory__item_blue,children:K.attention})]})]})})})]})},[x]);return(0,e.jsxs)("div",{className:Y.wrapper,children:[h&&E(),x?p?ce:W:F]})},ve=an,me={search:"search___kvGWZ",search__btn:"search__btn___IeAqs",search__btn_insert:"search__btn_insert___uWpFj",search_area:"search_area___oVSnI",search__multiple:"search__multiple___Ascb8"},sn=Ie.Z.TextArea,cn='{"content":"\u6211\u662F\u4E00\u4E2A\u597D\u4EBA", "attention":75, "divide":["11", "22"]}',O=["qa","embedding","impress","strategy","memory","mission","gpt","doc"],on=function(t){var n=t.chatModel,r=t.dispatch,s=n.isConnect,u=(0,m.useState)(cn),h=M()(u,2),i=h[0],p=h[1],_=(0,m.useState)(!1),I=M()(_,2),y=I[0],x=I[1],w=(0,m.useState)(!1),P=M()(w,2),D=P[0],k=P[1],G=(0,m.useState)(!1),F=M()(G,2),E=F[0],W=F[1],ce=(0,m.useState)(O[0]),B=M()(ce,2),R=B[0],ne=B[1],ae=Re.ZP.useMessage(),K=M()(ae,2),N=K[0],ie=K[1],xe=function(c){return new Promise(function(d,g){if(!s){N.warning("\u5F53\u524Dwebsocket\u79BB\u7EBF\uFF0C\u8BF7\u5148\u5EFA\u7ACB\u8FDE\u63A5"),d(null);return}if(!c){d(null);return}var C=U(),S=C.chatUid;(0,Z.gM)({uid:S,method:"get_task_context",seq:"2333",data:{task_id:c}}).then(function(v){if(v&&v.success){var A;d((A=v==null?void 0:v.task_context)!==null&&A!==void 0?A:{})}else d(null)})})},je=function(c){return new Promise(function(d,g){if(!s){N.warning("\u5F53\u524Dwebsocket\u79BB\u7EBF\uFF0C\u8BF7\u5148\u5EFA\u7ACB\u8FDE\u63A5"),d(null);return}if(!c){d(null);return}var C=U(),S=C.chatUid;(0,Z.HD)({uid:S,method:"get_llm_result",seq:"2333",data:{task_id:c}}).then(function(v){if(v&&v.success){var A,J;d((A=v==null||(J=v.data)===null||J===void 0?void 0:J.result)!==null&&A!==void 0?A:{})}else d(null)})})},Se=function(c){return new Promise(function(d,g){if(!s){N.warning("\u5F53\u524Dwebsocket\u79BB\u7EBF\uFF0C\u8BF7\u5148\u5EFA\u7ACB\u8FDE\u63A5"),d(null);return}if(!c){d(null);return}var C=U(),S=C.chatUid;(0,Z.HD)({uid:S,method:"get_qa_by_content",seq:"2333",data:{content:c}}).then(function(v){if(v&&v.success){var A,J;d((A=v==null||(J=v.data)===null||J===void 0?void 0:J.result)!==null&&A!==void 0?A:{})}else d(null)})})},Fe=function(c){return new Promise(function(d,g){if(!s){N.warning("\u5F53\u524Dwebsocket\u79BB\u7EBF\uFF0C\u8BF7\u5148\u5EFA\u7ACB\u8FDE\u63A5"),d(null);return}if(!c){d(null);return}var C=U(),S=C.chatUid;(0,Z.HD)({uid:S,method:"get_memory_by_content",seq:"2333",data:{content:c}}).then(function(v){if(v&&v.success){var A,J;d((A=v==null||(J=v.data)===null||J===void 0?void 0:J.result)!==null&&A!==void 0?A:{})}else d(null)})})},be=function(){return new Promise(function(c,d){if(!s){c(null);return}var g=U(),C=g.chatUid;(0,Z.rO)({uid:C}).then(function(S){if(S&&S.success){var v;c((v=S==null?void 0:S.data)!==null&&v!==void 0?v:{})}else c(null)})})},Me=function(){return new Promise(function(c,d){if(!s){c(null);return}var g=U(),C=g.chatUid;(0,Z.kg)({robot_id:"agent001",limit:100,uids:[C]}).then(function(S){if(S&&S.success){var v;c((v=S==null?void 0:S.data)!==null&&v!==void 0?v:{})}else c(null)})})},V=function(c){return new Promise(function(d,g){if(!s){N.warning("\u5F53\u524Dwebsocket\u79BB\u7EBF\uFF0C\u8BF7\u5148\u5EFA\u7ACB\u8FDE\u63A5"),d(null);return}if(!c){d(null);return}var C=U(),S=C.chatUid;(0,Z.wb)({uid:S,limit:50,cursor:0,type:c}).then(function(v){if(v&&v.success){var A;d((A=v==null?void 0:v.data)!==null&&A!==void 0?A:{})}else d(null)})})},ye=[{key:O[0],label:"QA\u68C0\u7D22",children:(0,e.jsx)(ve,{name:"QA\u68C0\u7D22",visible:R===O[0],action:Se,search:!0,tips:"\u8BF7\u8F93\u5165QA\u68C0\u7D22\u6761\u4EF6"})},{key:O[1],label:"\u957F\u671F\u8BB0\u5FC6embedding",children:(0,e.jsx)(ve,{name:"\u957F\u671F\u8BB0\u5FC6embedding",visible:R===O[1],action:Fe,search:!0,tips:"\u8BF7\u8F93\u5165\u957F\u671F\u8BB0\u5FC6\u68C0\u7D22\u6761\u4EF6"})},{key:O[2],label:"\u5370\u8C61\u67E5\u8BE2",children:(0,e.jsx)(ve,{name:"\u5370\u8C61\u67E5\u8BE2",visible:R===O[2],action:be})},{key:O[3],label:"\u7B56\u7565\u67E5\u8BE2",children:(0,e.jsx)(ve,{name:"\u7B56\u7565\u67E5\u8BE2",visible:R===O[3],action:Me})},{key:O[4],label:"\u8BB0\u5FC6\u67E5\u8BE2",children:(0,e.jsx)(ve,{name:"\u8BB0\u5FC6\u67E5\u8BE2",visible:R===O[4],search:!0,isMemory:!0,action:V})},{key:O[5],label:"\u4EFB\u52A1\u4E0A\u4E0B\u6587",children:(0,e.jsx)(ve,{name:"\u4EFB\u52A1\u4E0A\u4E0B\u6587",visible:R===O[5],action:xe,search:!0,tips:"\u8BF7\u8F93\u5165task_id"})},{key:O[6],label:"\u4EFB\u52A1\u5927\u6A21\u578B\u56DE\u590D",children:(0,e.jsx)(ve,{name:"\u4EFB\u52A1\u5927\u6A21\u578B\u56DE\u590D",visible:R===O[6],action:je,search:!0,tips:"\u8BF7\u8F93\u5165task_id"})},{key:O[7],label:"\u6587\u6863\u64CD\u4F5C\u4E0E\u67E5\u8BE2",children:(0,e.jsx)(tn,{visible:R===O[7]})}],ue=function(c){var d=c.target.value;p(d)},Ce=function(c){ne(c)},De=function(){if(!(!i||!i.trim())){var c={};try{c=JSON.parse(i)}catch(C){N.error("JSON\u89E3\u6790\u5931\u8D25\uFF0C\u8BF7\u68C0\u67E5\u8F93\u5165\u5185\u5BB9");return}k(!0);var d=U(),g=d.chatUid;(0,Z.HD)({uid:g,method:"insert_stream",seq:"2333",data:c}).then(function(C){C&&C.success?N.success("\u601D\u7EEA\u63D2\u5165\u6210\u529F"):Ae.Z.error({title:"\u5931\u8D25",content:C.msg?C.msg:"\u601D\u7EEA\u63D2\u5165\u5931\u8D25",okText:"\u786E\u5B9A"}),k(!1)}).catch(function(C){k(!1)})}},ke=function(){if(!i||!i.trim()){N.warning("\u8BF7\u8F93\u5165\u7B56\u7565\u5185\u5BB9");return}x(!0);var c=U(),d=c.chatUid;(0,Z.iZ)({uid:d,content:i,robot_id:"agent001",attention:60}).then(function(g){g&&g.success?N.success("\u7B56\u7565\u63D2\u5165\u6210\u529F"):Ae.Z.error({title:"\u5931\u8D25",content:g.msg?g.msg:"\u7B56\u7565\u63D2\u5165\u5931\u8D25",okText:"\u786E\u5B9A"}),x(!1)}).catch(function(g){x(!1)})},Ee=function(){if(!i||!i.trim()){N.warning("\u8BF7\u8F93\u5165\u89D2\u8272\u5185\u5BB9");return}W(!0);var c=U(),d=c.chatUid;(0,Z.HD)({uid:d,method:"set_role_transform",seq:"2333",data:{content:i}}).then(function(g){g&&g.success?(N.success("\u5207\u6362\u89D2\u8272\u6210\u529F"),r({type:"chatModel/fetchGetRole",payload:{uid:d,method:"get_robot_role",seq:"2333"}})):Ae.Z.error({title:"\u5931\u8D25",content:g.msg?g.msg:"\u5207\u6362\u89D2\u8272\u5931\u8D25",okText:"\u786E\u5B9A"}),W(!1)}).catch(function(g){W(!1)})};return(0,e.jsxs)("div",{className:me.search,children:[(0,e.jsx)(sn,{className:me.search_area,placeholder:"\u8BF7\u8F93\u5165\u7B56\u7565/JSON\u683C\u5F0F\u601D\u7EEA\u6D41",value:i,onChange:ue,autoSize:{minRows:4,maxRows:4}}),(0,e.jsxs)("div",{className:me.search__btn,children:[(0,e.jsx)(se.ZP,{className:me.search__btn_insert,type:"primary",disabled:!s||y||E,loading:D,onClick:De,children:"\u63D2\u5165\u601D\u7EEA\u6D41"}),(0,e.jsx)(se.ZP,{className:me.search__btn_insert,type:"primary",disabled:!s||D||E,onClick:ke,loading:y,children:"\u63D2\u5165\u7B56\u7565"}),(0,e.jsx)(se.ZP,{className:me.search__btn_insert,type:"primary",disabled:!s||D||y,onClick:Ee,loading:E,children:"\u6539\u53D8\u89D2\u8272"})]}),(0,e.jsx)("div",{className:me.search__multiple,children:(0,e.jsx)(ot.Z,{value:R,onChange:Ce,items:ye})}),ie]})},ln=(0,oe.connect)(function(o){var t=o.chatModel;return{chatModel:t}})(on),pe={wrapper:"wrapper___k564j",content:"content___LEixu",main:"main___PTQMg",onlyPc:"onlyPc___v51Cl"};function rn(){return(0,e.jsxs)("div",{className:pe.wrapper,children:[(0,e.jsx)("div",{className:"".concat(pe.content," ").concat(pe.main),children:(0,e.jsx)(Lt,{})}),(0,e.jsx)("div",{className:"".concat(pe.content," ").concat(pe.onlyPc),children:(0,e.jsx)(Yt,{})}),(0,e.jsx)("div",{className:"".concat(pe.content," ").concat(pe.onlyPc),children:(0,e.jsx)(ln,{})})]})}}}]);
