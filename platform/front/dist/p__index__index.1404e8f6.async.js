"use strict";(self.webpackChunk=self.webpackChunk||[]).push([[610],{93612:function(xn,at,v){v.r(at),v.d(at,{default:function(){return _n}});var ht=v(5574),C=v.n(ht),F=v(53343),Y=v(91222),_t=v(79928),oe=v(86111),vt=v(15009),Le=v.n(vt),ft=v(99289),it=v.n(ft),mt=v(19632),st=v.n(mt),pt=v(72004),yt=v.n(pt),gt=v(12444),xt=v.n(gt),jt=v(9783),X=v.n(jt),St=yt()(function c(){xt()(this,c),X()(this,"items",[]),X()(this,"enqueue",function(t){this.items.push(t)}),X()(this,"dequeue",function(){return this.items.shift()}),X()(this,"splice",function(t){items=[].concat(st()(this.items),st()(t))}),X()(this,"sort",function(t){this.items.sort(function(n,r){return n[t]-r[t]})}),X()(this,"checkFront",function(t,n){return this.items.slice(t,n)}),X()(this,"front",function(){return this.items[0]}),X()(this,"isEmpty",function(){return this.items.length===0}),X()(this,"clear",function(){this.items=[]}),X()(this,"size",function(){return this.items.length}),X()(this,"print",function(){console.log(this.items.toString())})}),Ne=null,We=!1,ct=0,Pe=-1,he=new St;function bt(){Ne=new AudioContext({latencyHint:"balanced"})}function Re(c){var t=ct;ct++,(0,F.sY)({text:c}).then(function(){var n=it()(Le()().mark(function r(o){var u;return Le()().wrap(function(i){for(;;)switch(i.prev=i.next){case 0:if(!(o&&o.status===200)){i.next=13;break}return i.prev=1,i.next=4,o.arrayBuffer();case 4:u=i.sent,we({arraybuffer:u,index:t}),i.next=11;break;case 8:i.prev=8,i.t0=i.catch(1),console.warn("tts\u89E3\u6790\u9519\u8BEF",i.t0);case 11:i.next=14;break;case 13:we({arraybuffer:null,index:t});case 14:case"end":return i.stop()}},r,null,[[1,8]])}));return function(r){return n.apply(this,arguments)}}()).catch(function(n){we({arraybuffer:null,index:t})})}function we(c){return Be.apply(this,arguments)}function Be(){return Be=it()(Le()().mark(function c(t){var n,r,o,u,h,i;return Le()().wrap(function(_){for(;;)switch(_.prev=_.next){case 0:if(n=t.arraybuffer,r=t.index,o=function(){if(!he.isEmpty()){var y=he.dequeue();we(y)}},!(!Ne||!(0,Y.eP)(n))){_.next=6;break}return Pe=r,o(),_.abrupt("return");case 6:if(!We){_.next=10;break}he.enqueue({arraybuffer:n,index:r}),_.next=27;break;case 10:if(r===Pe+1){_.next=17;break}he.enqueue({arraybuffer:n,index:r}),he.sort("index"),u=he.dequeue(),u.index===Pe+1?we(u):he.enqueue(u),_.next=27;break;case 17:return _.next=19,Ne.decodeAudioData(n);case 19:h=_.sent,i=Ne.createBufferSource(),i.buffer=h,i.connect(Ne.destination),i.onended=function(){We=!1,o()},i.start(0),We=!0,Pe=r;case 27:case"end":return _.stop()}},c)})),Be.apply(this,arguments)}function jn(){}function Sn(){Re("\u8FD9\u662F\u7B2C\u4E00\u53E5"),Re("\u4F60\u597D\uFF0C\u8FD9\u662F\u7B2C\u4E8C\u53E5,\u522B\u8D70\u5F00\u54E6"),Re("\u518D\u89C1")}var q=null,He=!1,_e="",Ke="",ve=(0,oe.getDvaApp)()._store.dispatch;function Ct(c){_e=c,q=new _t.Z({getAichatReqParams:function(n){return n}})}function Mt(c,t,n){if(!(!q||!_e)){var r=c!=null?c:"wss://agent.galaxyeye-tech.com/mts_agent/dialogue/v1/dialogue";q.setReconnect(!1),q.createConnect("".concat(r,"?uid=").concat(_e)),q.onStatusChange(function(o){var u=o.websocketIsOk;console.log("[ws] status changed:",u),He=u,ve({type:"chatModel/setChatModel",payload:{isConnect:u}}),u&&(0,Y.mf)(t)&&t(),!u&&(0,Y.mf)(n)&&n()}),q.onMessage(function(o){console.log("%c [ws] ack message:","color: #07c160; font-size: 14px",o)}),q.onUnknownMethod(function(o){var u=o.type,h=o.data,i=h===void 0?{}:h,p=o.task_id;if(console.log("%c [ws] unKnow ack message:","color: #0ca1f7; font-size: 14px",o),u==="\u601D\u7EEA\u6D41\u6D88\u606F")ve({type:"chatModel/setMindStreamList",payload:{message:i}});else if(u==="\u610F\u56FE\u5207\u6362"){var _;ve({type:"chatModel/setChatModel",payload:{intention:(_=i.main_task)!==null&&_!==void 0?_:"\u5F53\u524D\u6682\u65E0\u610F\u56FE"}})}else if(u==="\u4EFB\u52A1\u5207\u6362")Ke=p,ve({type:"chatModel/fetchGetMissionDetail",payload:{uid:_e,method:"get_task_context",seq:"2333",data:{task_id:p}}});else if((i==null?void 0:i.target)==="\u8868\u8FBE\u7BA1\u7406"){var A=(0,oe.getDvaApp)()._store.getState(),y=A.chatModel,x=y===void 0?{}:y,k=x.isMute;!k&&i&&i.content&&(0,Y.HD)(i.content)&&Re(i.content),ve({type:"chatModel/setChatList",payload:{message:{data:i,type:"ai"}}})}else p&&(Ke=p,ve({type:"chatModel/fetchGetMissionDetail",payload:{uid:_e,method:"get_task_context",seq:"2333",data:{task_id:p}}}))}),q.onError(function(o){console.log("%c [ws] error:","color: #fd9090; font-size: 14px",JSON.stringify(o))})}}function bn(){q.closeConnect()}function ot(c){if(!(!q||!He)){var t={uid:_e,method:"input",data:{content:c},seq:"2333"};q.sendMessage(t),t.type="user",ve({type:"chatModel/setChatList",payload:{message:t}})}}function U(){return{isConnected:He,chatUid:_e,taskId:Ke}}var $=void 0,De=!1,kt=function(t){var n=JSON.parse(t.data);if(console.log("[asr] msg",n),n&&n.code===0){var r=n.result,o=r.slice_type,u=r.voice_text_str;o===2&&ot(u)}else{var h;console.warn("[asr] \u9519\u8BEF\u6D88\u606F",(h=n==null?void 0:n.message)!==null&&h!==void 0?h:"\u65E0")}};function Nt(c){var t=c.onClose,n=c.onError;if(De){console.log("[asr] \u8BF7\u52FF\u91CD\u590D\u8FDE\u63A5");return}$=new WebSocket("wss://agent.galaxyeye-tech.com/speech-service-atw/v1/wsasr"),$.binaryType="arraybuffer",$.onopen=function(){console.log("[asr] \u8FDE\u63A5\u6210\u529F"),De=!0},$.onmessage=kt,$.onerror=function(r){console.warn("[asr] \u8FDE\u63A5\u9519\u8BEF"),De=!1,(0,Y.mf)(n)&&n(r)},$.onclose=function(){console.warn("[asr] \u8FDE\u63A5\u5173\u95ED"),De=!1,(0,Y.mf)(t)&&t()}}function lt(){$&&De&&($.close(),$=void 0)}function wt(c){$&&$.send(c)}var Dt=v(57584),Ge=v.n(Dt),Cn=v(10884),Mn=v(27538),le=null,Ve=null;function It(c){var t=c!=null?c:{},n=t.type,r=n===void 0?"pcm":n,o=t.bitRate,u=o===void 0?16:o,h=t.sampleRate,i=h===void 0?16e3:h,p=t.process,_=p===void 0?function(){}:p,A=function(x,k,R,E){Ve&&Ve.input(x[x.length-1],k,E),(0,Y.mf)(_)&&_(Ge().SampleData(x.slice(-1),E,i).data)};le=new(Ge())({type:r,bitRate:u,sampleRate:i,onProcess:A})}function At(c){Ve=Ge().WaveView(c)}function Et(c){if(!le){console.log("\u83B7\u53D6\u5F55\u97F3\u6743\u9650\u5931\u8D25\uFF0C\u672A\u521D\u59CB\u5316");return}var t=c!=null?c:{},n=t.success,r=n===void 0?function(){}:n,o=t.fail,u=o===void 0?function(){}:o,h=function(_){console.log("[Recorder H5] open success"),(0,Y.mf)(r)&&r(_)},i=function(_){console.log("[Recorder H5] open fail"),(0,Y.mf)(u)&&u(_)};le.open(h,i)}function kn(c){if(le){var t=c!=null?c:{},n=t.success,r=n===void 0?function(){}:n,o=function(h){console.log("[Recorder H5] close success"),isFunction(r)&&r(h)};le.close(o)}}function Tt(){le.start()}function Ut(c){if(le){var t=c!=null?c:{},n=t.success,r=n===void 0?function(){}:n,o=t.fail,u=o===void 0?function(){}:o,h=function(_){(0,Y.mf)(r)&&r(_)},i=function(_){(0,Y.mf)(u)&&u(_)};le.stop(h,i,!1)}}var Lt=v(35102),Pt=v(71965),Fe=v(68872),Ie=v(41202),Ae=v(23324),se=v(14726),Je=v(47153),Ye=v(96486),Rt=v(20091),m=v(67294),s={link:"link___VCmRN",link__input:"link__input___Lc8in",link__btn:"link__btn___a3gJz",point:"point___naUO2",point_inside:"point_inside___hsc3O",link_inside:"link_inside___J0xaj",disLink:"disLink___Olkku",disLink_inside:"disLink_inside___x1H34",mobile:"mobile___sy4aC",mobile2:"mobile2___Am0Tt",mobile3:"mobile3___Tqdbi",chat:"chat___YRMf0",chat__top:"chat__top___p2PQ6",chat__top__btn:"chat__top__btn___hE3u5",chat__top__btn_margin:"chat__top__btn_margin___nIF68",chat__top__btn_voice:"chat__top__btn_voice___Gq6ST",voiceOn:"voiceOn___M20h8",voiceOff:"voiceOff___MKs98",chat__intention:"chat__intention___cKdZ0",chat__intention_title:"chat__intention_title___rbz93",chat__intention_text:"chat__intention_text___yDB5D",chat__content:"chat__content___vd_jq",user:"user___p1tXs",ai:"ai___vXkbg",item:"item___Iey9r",item__icon_user:"item__icon_user___kXxLe",item__icon_ai:"item__icon_ai___aMdQ3",item__text:"item__text___G616U",item__text_time:"item__text_time___pf1vX",right:"right___Xf3f6",item__text_content:"item__text_content___mKBVx",chat__content_line:"chat__content_line___PzX1s",chat__input:"chat__input___fLbky",chat__input_area:"chat__input_area___NdxTQ",chat__input_btn:"chat__input_btn___ypUAL",chat__input_switch:"chat__input_switch___KT4Be",cube:"cube___PCVMV",talk:"talk___RIB1U",chat__input_micro:"chat__input_micro___RrHGy"},e=v(85893),Ft={elem:".recorderWave",width:500,height:30,keep:!1,lineWidth:2,scale:1,phase:21.8},Ot=function(t){var n=t.chatModel,r=t.dispatch,o=n.chatList,u=n.historyChatList,h=n.isConnect,i=n.intention,p=n.isMute,_=Fe.ZP.useMessage(),A=C()(_,2),y=A[0],x=A[1],k=(0,m.useState)(!0),R=C()(k,2),E=R[0],N=R[1],K=(0,m.useState)(""),O=C()(K,2),T=O[0],W=O[1],ce=(0,m.useState)("wss://agent.galaxyeye-tech.com/mts_agent/dialogue/v1/dialogue"),B=C()(ce,2),L=B[0],ne=B[1],ae=(0,m.useState)(""),J=C()(ae,2),w=J[0],ie=J[1],xe=(0,m.useState)(!1),je=C()(xe,2),Se=je[0],Ee=je[1],be=(0,m.useState)(!1),Ce=C()(be,2),G=Ce[0],ue=Ce[1],de=(0,m.useRef)(),Me=new Rt.Z({html:!1,linkify:!0,typographer:!1});(0,m.useEffect)(function(){It({process:function(a){wt(a.buffer)}}),bt()},[]),(0,m.useEffect)(function(){localStorage.setItem("MTS_TOOL_AUDIO_STATE",p?"true":"false")},[p]),(0,m.useEffect)(function(){de.current&&(de.current.scrollTop=de.current.scrollHeight)},[o,u]),(0,m.useEffect)(function(){G?(Nt({onClose:function(){ue(!1)},onError:function(a){console.warn("[asr] \u8FDE\u63A5\u610F\u5916\u65AD\u5F00",a),y.error("ASR\u8FDE\u63A5\u5DF2\u65AD\u5F00")}}),At(Ft),Et({success:function(){console.log("\u9EA6\u514B\u98CE\u6743\u9650\u83B7\u53D6\u6210\u529F\uFF0Copen"),Tt()},fail:function(a){y.error(a!=null?a:"\u83B7\u53D6\u9EA6\u514B\u98CE\u6743\u9650\u5931\u8D25"),lt(),ue(!1)}})):(lt(),Ut())},[G]);var Te=function(){if(!T){y.warning("\u8BF7\u8F93\u5165uid");return}if(!L){y.warning("\u8BF7\u8F93\u5165url");return}var a=function(){y.success("\u8FDE\u63A5\u6210\u529F"),j(),l(),d(),g()},D=function(){y.error("\u8FDE\u63A5\u65AD\u5F00")};Ct(T),Mt(L,a,D)},ke=function(){if(!h){y.warning("\u5F53\u524Dwebsocket\u79BB\u7EBF\uFF0C\u8BF7\u5148\u521B\u5EFA\u8FDE\u63A5");return}if(!w||!w.trim()){ie("");return}ot(w),ie("")},Ue=(0,Ye.debounce)(function(b){var a=b.target.value?"\u7EFF\u706F":"\u7EA2\u706F",D=U(),P=D.chatUid;(0,F.HD)({uid:P,method:"set_exp_status",seq:"2333",data:{status:a}}).then(function(H){if(H&&H.success)y.success("\u5207\u6362\u6210\u529F"),N(b.target.value),r({type:"chatModel/setChatList",payload:{message:{type:"line",content:"\u5DF2\u5207\u6362\u4E3A".concat(a)}}});else{var te;y.error((te=H==null?void 0:H.msg)!==null&&te!==void 0?te:"\u5207\u6362\u5931\u8D25")}})},1e3),j=function(){var a=U(),D=a.chatUid;(0,F.HD)({uid:D,method:"get_exp_status",seq:"2333"}).then(function(P){if(P&&P.success){var H=P.data.status;N(H==="\u7EFF\u706F")}})},l=function(){var a=U(),D=a.chatUid;r({type:"chatModel/fetchGetHistoryChat",payload:{uid:D,method:"get_history_dialog",seq:"2333"}})},d=function(){var a=U(),D=a.chatUid;r({type:"chatModel/fetchGetRole",payload:{uid:D,method:"get_robot_role",seq:"2333"}})},g=function(){var a=U(),D=a.chatUid;r({type:"chatModel/fetchGetIntention",payload:{uid:D,method:"get_intention",seq:"2333",data:{}}})},M=function(){var a=U(),D=a.chatUid;if(!h){y.warning("\u5F53\u524Dwebsocket\u79BB\u7EBF\uFF0C\u8BF7\u5148\u521B\u5EFA\u8FDE\u63A5");return}Ie.Z.confirm({title:"\u63D0\u793A",content:"\u662F\u5426\u6E05\u9664\u5BF9\u8BDD\u8BB0\u5F55",cancelText:"\u53D6\u6D88",okText:"\u6E05\u9664",onOk:(0,Ye.debounce)(function(){(0,F.gM)({uid:D,method:"clear_dialogue_history",seq:"2333"}).then(function(P){var H=P.success;if(H)y.success("\u6E05\u9664\u5BF9\u8BDD\u6210\u529F"),r({type:"chatModel/setChatList",payload:{message:{type:"line",content:"\u4EE5\u4E0A\u5BF9\u8BDD\u5DF2\u6E05\u9664"}}});else{var te;y.error((te=P==null?void 0:P.msg)!==null&&te!==void 0?te:"\u6E05\u9664\u5931\u8D25")}})},500)})},S=(0,Ye.debounce)(function(){if(!h){y.warning("\u5F53\u524Dwebsocket\u79BB\u7EBF\uFF0C\u8BF7\u5148\u521B\u5EFA\u8FDE\u63A5");return}var b=U(),a=b.chatUid;(0,F.HD)({uid:a,method:"clear_robot_role",seq:"2333"}).then(function(D){var P=D.success;if(P)y.success("\u6E05\u9664\u89D2\u8272\u6210\u529F"),r({type:"chatModel/setChatList",payload:{message:{type:"line",content:"\u5F53\u524D\u89D2\u8272\u5DF2\u91CD\u7F6E"}}}),r({type:"chatModel/setChatModel",payload:{globalRole:""}});else{var H;y.error((H=D==null?void 0:D.msg)!==null&&H!==void 0?H:"\u6E05\u9664\u5931\u8D25")}})},500),f=function(){G?ue(!1):Ee(function(a){return!a})},I=function(){if(!h){y.warning("\u5F53\u524Dwebsocket\u79BB\u7EBF\uFF0C\u8BF7\u5148\u521B\u5EFA\u8FDE\u63A5");return}G||ue(!0)},V=function(){r({type:"chatModel/setChatModel",payload:{isMute:!p}})},vn=function(a,D){var P=a.role;return P==="user"?(0,e.jsxs)("div",{className:"".concat(s.item," ").concat(s.user),children:[(0,e.jsxs)("div",{className:s.item__text,children:[(0,e.jsx)("div",{className:"".concat(s.item__text_time," ").concat(s.right),children:"--"}),(0,e.jsx)("div",{className:s.item__text_content,children:a==null?void 0:a.content})]}),(0,e.jsx)("div",{className:s.item__icon_user})]},D):(0,e.jsxs)("div",{className:"".concat(s.item," ").concat(s.ai),children:[(0,e.jsx)("div",{className:s.item__icon_ai}),(0,e.jsxs)("div",{className:s.item__text,children:[(0,e.jsx)("div",{className:s.item__text_time,children:"--"}),(0,e.jsx)("div",{className:s.item__text_content,dangerouslySetInnerHTML:{__html:Me.renderInline((0,Y.HD)(a==null?void 0:a.content)?a==null?void 0:a.content:" ")}})]})]},D)},fn=function(a,D){var P=a.type,H=a.currentRole;if(P==="user"){var te,$e;return(0,e.jsxs)("div",{className:"".concat(s.item," ").concat(s.user),children:[(0,e.jsxs)("div",{className:s.item__text,children:[(0,e.jsx)("div",{className:"".concat(s.item__text_time," ").concat(s.right),children:(te=a==null?void 0:a.time)!==null&&te!==void 0?te:""}),(0,e.jsx)("div",{className:s.item__text_content,children:a==null||($e=a.data)===null||$e===void 0?void 0:$e.content})]}),(0,e.jsx)("div",{className:s.item__icon_user})]},D)}if(P==="ai"){var et,tt,nt;return(0,e.jsxs)("div",{className:"".concat(s.item," ").concat(s.ai),children:[(0,e.jsx)("div",{className:s.item__icon_ai}),(0,e.jsxs)("div",{className:s.item__text,children:[(0,e.jsxs)("div",{className:s.item__text_time,children:[(0,e.jsx)("span",{children:H?"<".concat(H,">"):""}),(et=a==null?void 0:a.time)!==null&&et!==void 0?et:""]}),(0,e.jsx)("div",{className:s.item__text_content,dangerouslySetInnerHTML:{__html:Me.renderInline((0,Y.HD)(a==null||(tt=a.data)===null||tt===void 0?void 0:tt.content)?a==null||(nt=a.data)===null||nt===void 0?void 0:nt.content:" ")}})]})]},D)}if(P==="line"&&a.content)return(0,e.jsx)("div",{className:s.chat__content_line,children:a.content})},mn=function(){return(0,e.jsx)("div",{className:s.chat__content_line,children:"----------------\u4EE5\u4E0A\u4E3A\u5386\u53F2\u5BF9\u8BDD----------------"})},pn=(0,e.jsx)("div",{className:"".concat(s.point," ").concat(h?s.link:s.disLink),children:(0,e.jsx)("div",{className:"".concat(s.point_inside," ").concat(h?s.link_inside:s.disLink_inside)})}),yn=function(){return(0,e.jsxs)(m.Fragment,{children:[(0,e.jsx)("div",{className:s.chat__input_switch,onClick:f,children:(0,e.jsx)(Lt.Z,{})}),(0,e.jsx)(Ae.Z,{className:s.chat__input_area,placeholder:"\u8BF7\u8F93\u5165\u5BF9\u8BDD\u5185\u5BB9",value:w,onChange:function(D){ie(D.target.value)},onPressEnter:ke}),(0,e.jsx)(se.ZP,{className:s.chat__input_btn,type:"primary",onClick:ke,children:"\u53D1\u9001"})]})},gn=function(){return(0,e.jsxs)(m.Fragment,{children:[(0,e.jsx)("div",{className:"".concat(s.chat__input_switch," ").concat(G?s.talk:""),onClick:f,children:G?(0,e.jsx)("div",{className:s.cube}):(0,e.jsx)(Pt.Z,{})}),(0,e.jsx)("div",{className:s.chat__input_micro,onClick:I,children:G?(0,e.jsx)("div",{class:"recorderWave",style:{width:"540px",height:"30px"}}):"\u5F00\u59CB\u8BF4\u8BDD"})]})};return(0,e.jsxs)(m.Fragment,{children:[(0,e.jsxs)("div",{className:s.link,children:[(0,e.jsx)(Ae.Z,{placeholder:"\u8BF7\u8F93\u5165uid",className:"".concat(s.link__input," ").concat(s.mobile),value:T,onChange:function(a){W(a.target.value)}}),(0,e.jsx)(Ae.Z,{placeholder:"\u8BF7\u8F93\u5165url",className:"".concat(s.link__input," ").concat(s.mobile2),value:L,onChange:function(a){ne(a.target.value)}}),(0,e.jsx)(se.ZP,{type:"primary",icon:pn,ghost:!0,className:"".concat(s.link__btn," ").concat(s.mobile3),onClick:Te,children:h?"\u5DF2\u8FDE\u63A5":"\u8FDE\u63A5"})]}),(0,e.jsxs)("div",{className:s.chat,children:[(0,e.jsxs)("div",{className:s.chat__top,children:[(0,e.jsxs)("div",{className:s.chat__top__btn,children:[(0,e.jsx)(se.ZP,{type:"primary",ghost:!0,onClick:M,children:"\u6E05\u9664\u5BF9\u8BDD\u8BB0\u5F55"}),(0,e.jsx)(se.ZP,{type:"primary",className:s.chat__top__btn_margin,ghost:!0,onClick:S,children:"\u6E05\u9664\u5F53\u524D\u89D2\u8272"}),(0,e.jsx)("div",{className:"".concat(s.chat__top__btn_voice," ").concat(p?s.voiceOff:s.voiceOn),title:p?"\u5F00\u542F\u8BED\u97F3\u5408\u6210":"\u9759\u97F3",onClick:V})]}),(0,e.jsxs)(Je.ZP.Group,{value:E,onChange:Ue,disabled:!h,children:[(0,e.jsx)(Je.ZP,{value:!1,children:"\u7EA2\u706F"}),(0,e.jsx)(Je.ZP,{value:!0,children:"\u7EFF\u706F"})]})]}),h&&(0,e.jsxs)("div",{className:s.chat__intention,children:[(0,e.jsx)("div",{className:s.chat__intention_title,children:"\u610F\u56FE\uFF1A"}),(0,e.jsx)("div",{className:s.chat__intention_text,children:i})]}),(0,e.jsxs)("div",{className:s.chat__content,ref:de,children:[u.map(function(b,a){return vn(b,a)}),u.length>0&&mn(),o.map(function(b,a){return fn(b,a)})]}),(0,e.jsx)("div",{className:s.chat__input,children:Se?gn():yn()})]}),x]})},Zt=(0,oe.connect)(function(c){var t=c.chatModel;return{chatModel:t}})(Ot),Wt=v(72269),rt=v(57135),Bt=v(27484),Qe=v.n(Bt),ee={wrapper:"wrapper___nnTjx",empty:"empty___VfKKj",mind:"mind___RiYB7",item:"item___H_SFj",item_key:"item_key___Y0BwJ",item_value:"item_value___Y0aZ5",enhance:"enhance___AtFB2",time:"time___Fu0nd"},Ht=["content","source","target","response","attention","msg"],Kt=["response","msg","content"],Gt=function(t){var n=t.chatModel,r=t.isSimplify,o=r===void 0?!1:r,u=n.mindStream;(0,m.useEffect)(function(){},[u]);var h=(0,e.jsx)("div",{className:ee.empty,children:"\u6682\u65E0\u601D\u7EEA\u6D41"}),i=function(_,A){var y=function(N){var K=null;N.time?(K=N.time,delete N.time):K=Qe()().format("HH:mm:ss");var O=Object.entries(N);return o&&(O=O.filter(function(T){var W=C()(T,2),ce=W[0],B=W[1];return Ht.includes(ce)})),{time:K,resList:O}},x=y(JSON.parse(JSON.stringify(_))),k=x.time,R=x.resList;return(0,e.jsxs)("div",{className:ee.mind,children:[(0,e.jsxs)("div",{className:"".concat(ee.item," ").concat(ee.time),children:[(0,e.jsx)("div",{className:ee.item_key,children:"\u65F6\u95F4"}),(0,e.jsx)("div",{className:ee.item_value,children:k!=null?k:"--"})]}),R.map(function(E,N){return(0,e.jsxs)("div",{className:ee.item,children:[(0,e.jsx)("div",{className:ee.item_key,children:"".concat(E[0],":")}),(0,e.jsx)("div",{className:"".concat(ee.item_value," ").concat(Kt.includes(E[0])?ee.enhance:""),children:JSON.stringify(E[1])})]},N)})]},A)};return(0,e.jsx)("div",{className:ee.wrapper,children:u.length>0?u.map(function(p,_){return i(p,_)}):h})},Vt=(0,oe.connect)(function(c){var t=c.chatModel;return{chatModel:t}})(Gt),ze=v(2096),Jt=v(55171),Xe=v.n(Jt),fe={wrapper:"wrapper___q8ufk",empty:"empty___ltA1p",detail:"detail___MD_ag",detail__id:"detail__id___HjaLl",detail__id_title:"detail__id_title___dcYTg",detail__id_num:"detail__id_num___KbyHe",detail__json:"detail__json___ANb4P"},Yt=function(t){var n=t.chatModel,r=t.visible,o=t.dispatch,u=n.missionDetail,h=n.missionId,i=(0,m.useState)(!1),p=C()(i,2),_=p[0],A=p[1],y=Fe.ZP.useMessage(),x=C()(y,2),k=x[0],R=x[1];(0,m.useEffect)(function(){if(r){var O=U(),T=O.chatUid,W=O.taskId;T&&W&&o({type:"chatModel/fetchGetMissionDetail",payload:{uid:T,method:"get_task_context",seq:"2333",data:{task_id:W}}})}},[r]),(0,m.useEffect)(function(){u&&Object.keys(u).length>0?A(!0):A(!1)},[u]);var E=function(){try{if(navigator.clipboard)navigator.clipboard.writeText(h).then(function(){k.success("\u590D\u5236\u6210\u529F")});else{var T=document.createElement("textarea");document.body.appendChild(T),T.value=h,T.select(),document.execCommand("copy")&&(document.execCommand("copy"),k.success("\u590D\u5236\u6210\u529F")),document.body.removeChild(T)}}catch(W){k.error("\u5F53\u524D\u6D4F\u89C8\u5668\u4E0D\u652F\u6301\u590D\u5236\uFF0C\u8BF7\u624B\u52A8\u590D\u5236")}},N=(0,e.jsx)("div",{className:fe.empty,children:"\u6682\u65E0\u4EFB\u52A1\u4FE1\u606F"}),K=function(){return(0,e.jsxs)("div",{className:fe.detail,children:[h?(0,e.jsxs)("div",{className:fe.detail__id,children:[(0,e.jsx)("div",{className:fe.detail__id_title,children:"task_id:"}),(0,e.jsx)(ze.Z,{title:"\u70B9\u51FB\u590D\u5236",children:(0,e.jsx)("div",{className:fe.detail__id_num,onClick:E,children:h})})]}):null,(0,e.jsx)("div",{className:fe.detail__json,children:(0,e.jsx)(Xe(),{src:u,name:"\u5F53\u524D\u4EFB\u52A1\u4FE1\u606F",collapsed:1,displayDataTypes:!1})}),R]})};return(0,e.jsx)("div",{className:fe.wrapper,children:_?K():N})},Qt=(0,oe.connect)(function(c){var t=c.chatModel;return{chatModel:t}})(Yt),qe={wrapper:"wrapper___jTwi3",empty:"empty___rbKTQ",detail:"detail___ep9gi"},zt=function(t){var n=t.chatModel,r=t.visible,o=t.dispatch,u=n.workMemory,h=(0,m.useState)(!1),i=C()(h,2),p=i[0],_=i[1];(0,m.useEffect)(function(){r&&A()},[r]),(0,m.useEffect)(function(){u&&Object.keys(u).length>0?_(!0):_(!1)},[u]);var A=function(){var R=U(),E=R.isConnected,N=R.chatUid;E&&N&&o({type:"chatModel/fetchGetWorkMemory",payload:{uid:N,method:"get_work_memory",seq:"2333"}})},y=(0,e.jsx)("div",{className:qe.empty,children:"\u6682\u65E0\u5DE5\u4F5C\u8BB0\u5FC6"}),x=function(){return(0,e.jsx)("div",{className:qe.detail,children:(0,e.jsx)(Xe(),{src:u,name:"\u5DE5\u4F5C\u8BB0\u5FC6",collapsed:1,displayDataTypes:!1})})};return(0,e.jsx)("div",{className:qe.wrapper,children:p?x():y})},Xt=(0,oe.connect)(function(c){var t=c.chatModel;return{chatModel:t}})(zt),ge={display:"display___X86X8",tab:"tab___AOdT_",switch:"switch___A2Y3L",stone:"stone___xTzlF"},re=["mind","mission","memory"];function qt(){var c=(0,m.useState)(re[0]),t=C()(c,2),n=t[0],r=t[1],o=(0,m.useState)(!1),u=C()(o,2),h=u[0],i=u[1],p=[{key:re[0],label:"\u601D\u7EEA\u6D41",children:(0,e.jsx)("div",{className:ge.tab,children:(0,e.jsx)(Vt,{isSimplify:h})})},{key:re[1],label:"\u5F53\u524D\u4EFB\u52A1\u4FE1\u606F",children:(0,e.jsx)("div",{className:ge.tab,children:(0,e.jsx)(Qt,{visible:n===re[1]})})},{key:re[2],label:"\u5DE5\u4F5C\u8BB0\u5FC6",children:(0,e.jsx)("div",{className:ge.tab,children:(0,e.jsx)(Xt,{visible:n===re[2]})})}],_=function(k){r(k)},A=(0,e.jsx)("div",{className:ge.stone}),y=(0,m.useMemo)(function(){var x=function(R){i(R)};return n===re[0]?(0,e.jsx)(Wt.Z,{className:ge.switch,value:h,checkedChildren:"\u7CBE\u7B80",unCheckedChildren:"\u666E\u901A",onChange:x}):A},[n,h]);return(0,e.jsx)("div",{className:ge.display,children:(0,e.jsx)(rt.Z,{defaultActiveKey:re[0],onChange:_,tabBarExtraContent:{left:y,right:A},centered:!0,items:p})})}var $t=v(97857),Oe=v.n($t),en=v(97937),tn=v(88484),nn=v(98165),an=v(55854),z={wrapper:"wrapper___wyzU9",upload:"upload___FMzEk",count:"count___dOpvt",count_text:"count_text___RrfRr",count_icon:"count_icon____mUFi",content:"content___KW54p",list:"list___erTI_",file:"file___KmD01",file_name:"file_name___lWJ7X",file_status:"file_status___YXUJv",file_time:"file_time___GX9rB",file_btn:"file_btn___cMoJr"},ut=void 0,Ze=null,sn=function(t){var n=t.visible,r=t.chatModel,o=r.isConnect,u=(0,m.useRef)(),h=Fe.ZP.useMessage(),i=C()(h,2),p=i[0],_=i[1],A=(0,m.useState)([]),y=C()(A,2),x=y[0],k=y[1],R=(0,m.useState)([]),E=C()(R,2),N=E[0],K=E[1],O=(0,m.useState)(0),T=C()(O,2),W=T[0],ce=T[1],B=(0,m.useState)(!1),L=C()(B,2),ne=L[0],ae=L[1],J=(0,m.useState)([]),w=C()(J,2),ie=w[0],xe=w[1],je=(0,m.useState)(!1),Se=C()(je,2),Ee=Se[0],be=Se[1],Ce=function(){var j;return function(l,d){return j||(j=l,d&&d(l)),{fileList:j,reset:function(){j=!1}}}}();(0,m.useEffect)(function(){return n&&(G(),Ze=setInterval(function(){G()},10*1e3)),function(){Ze&&(clearInterval(Ze),Ze=null)}},[n]),(0,m.useEffect)(function(){if(N.length>0){var j=U(),l=j.chatUid,d=new FormData;N.forEach(function(g){d.append("upload_files",g)}),d.append("confidence",50),d.append("uid",l),(0,F.Ki)(d).then(function(g){if(g&&g.success){var M=g.data,S=Object.values(M),f=S.filter(function(I){return I.err!==""});console.log("\u9519\u8BEF\u4FE1\u606F",f),f.length>0?(xe(f),be(!0)):p.success("\u4E0A\u4F20\u6210\u529F"),G()}else p.error("\u4E0A\u4F20\u5931\u8D25")}),u.current.reset(),K([])}},[N]);var G=function(l){var d=U(),g=d.chatUid,M=d.isConnected;g&&M&&(0,F.gf)({cursor:0,limit:100,uid:g}).then(function(S){if(S&&S.success){var f=S.data,I=f.total,V=f.infos;k(V),ce(I),l&&l(S)}})},ue=function(l){l&&l.success?p.success("\u5237\u65B0\u6210\u529F"):p.error("\u5237\u65B0\u5931\u8D25")},de=function(l){(0,F.cy)({ids:[l]}).then(function(d){d&&d.success?(p.success("\u5220\u9664\u6210\u529F"),G()):p.error("\u5220\u9664\u5931\u8D25")})},Me=function(l,d){var g,M={0:"\u5F85\u5904\u7406",1:"\u5904\u7406\u4E2D",2:"\u6210\u529F",3:"\u5931\u8D25"},S={0:"#000000",1:"#2c6fff",2:"#1d8b1d",3:"#ff2b2b"};return(0,e.jsxs)("div",{className:z.file,children:[(0,e.jsx)("div",{className:z.file_name,children:(0,e.jsx)(ze.Z,{title:l.name,children:l.name})}),(0,e.jsx)("div",{className:z.file_status,style:{color:S[l.status]},children:M[l.status]}),(0,e.jsx)("div",{className:z.file_time,children:Qe().unix(l.gmt_create).format("YYYY/M/D")}),(0,e.jsx)("div",{className:z.file_btn,onClick:de.bind(ut,l.id),children:(0,e.jsx)(en.Z,{})})]},(g=l.id)!==null&&g!==void 0?g:d)},Te=(0,m.useMemo)(function(){return(0,e.jsx)("ul",{children:ie.map(function(j,l){return(0,e.jsx)("li",{children:j.err},l)})})},[ie]),ke={accept:".doc,.docx",showUploadList:!1,multiple:!0,beforeUpload:function(l,d){return u.current=Ce(d,K),!1}},Ue={title:"\u4E0A\u4F20\u5F02\u5E38",open:Ee,closeIcon:!1,okText:"\u786E\u5B9A",cancelButtonProps:{style:{display:"none"}},onOk:function(){xe([]),be(!1)}};return(0,e.jsxs)("div",{className:z.wrapper,children:[(0,e.jsxs)("div",{className:z.upload,children:[(0,e.jsx)(an.Z,Oe()(Oe()({},ke),{},{children:(0,e.jsx)(ze.Z,{title:"\u76EE\u524D\u4EC5\u652F\u6301\u4E2D\u6587\u6587\u6863\uFF0C\u53EF\u6309\u4F4Fctrl\u591A\u9009",children:(0,e.jsx)(se.ZP,{disabled:!o,icon:(0,e.jsx)(tn.Z,{}),children:"\u70B9\u51FB\u4E0A\u4F20\u6587\u4EF6"})})})),(0,e.jsxs)("div",{className:z.count,children:[(0,e.jsx)("div",{className:z.count_text,children:"\u603B\u6570:".concat(W)}),(0,e.jsx)("div",{className:z.count_icon,onMouseEnter:function(){ae(!0)},onMouseLeave:function(){ae(!1)},onClick:G.bind(ut,ue),title:"\u5237\u65B0",children:(0,e.jsx)(nn.Z,{spin:ne})})]})]}),(0,e.jsx)("div",{className:z.content,children:(0,e.jsx)("div",{className:z.list,children:x.map(function(j){return Me(j)})})}),(0,e.jsx)(Ie.Z,Oe()(Oe()({},Ue),{},{children:Te})),_]})},cn=(0,oe.connect)(function(c){var t=c.chatModel;return{chatModel:t}})(sn),on=v(42192),Q={wrapper:"wrapper___lgB8c",detail:"detail___W5mat",detail__json:"detail__json___TNOfM",empty:"empty___ggOD8",input:"input___iBJjV",input_text:"input_text___DE9Rl",input_btn:"input_btn___pKojm",memory:"memory___MwtRi",memory_total:"memory_total___HIyQ0",memory__item:"memory__item___KnNjw",memory__item_content:"memory__item_content___wrG8T",memory__item_red:"memory__item_red___inZ4_",memory__item_blue:"memory__item_blue___ubbtW"},dt=[{value:"\u731C\u60F3",label:"\u731C\u60F3"},{value:"\u7528\u6237\u9648\u8FF0",label:"\u7528\u6237\u9648\u8FF0"},{value:"\u7ED3\u8BBA",label:"\u7ED3\u8BBA"}],ln=function(t){var n=t.visible,r=t.action,o=t.name,u=t.search,h=u===void 0?!1:u,i=t.isMemory,p=i===void 0?!1:i,_=t.tips,A=(0,m.useState)(null),y=C()(A,2),x=y[0],k=y[1],R=(0,m.useState)(p?dt[0].value:""),E=C()(R,2),N=E[0],K=E[1];(0,m.useEffect)(function(){n&&r&&!h&&r().then(function(B){B&&Object.keys(B).length>0?k(B):k(null)})},[n]);var O=(0,e.jsx)("div",{className:Q.empty,children:"\u6682\u65E0".concat(o)}),T=function(){var L=function(w){var ie=w.target.value;K(ie)},ne=function(w){K(w)},ae=function(){r(N).then(function(w){w&&Object.keys(w).length>0?k(w):k(null)})};return(0,e.jsxs)("div",{className:Q.input,children:[p?(0,e.jsx)(on.Z,{className:Q.input_text,options:dt,value:N,onChange:ne,placeholder:_!=null?_:"\u8BF7\u9009\u62E9\u68C0\u7D22\u6761\u4EF6"}):(0,e.jsx)(Ae.Z,{className:Q.input_text,value:N,onChange:L,placeholder:_!=null?_:"\u8BF7\u8F93\u5165\u68C0\u7D22\u6761\u4EF6"}),(0,e.jsx)(se.ZP,{className:Q.input_btn,type:"primary",onClick:ae,children:"\u67E5\u8BE2"})]})},W=(0,m.useMemo)(function(){return(0,e.jsx)("div",{className:Q.detail__json,children:(0,e.jsx)(Xe(),{src:x,name:o,collapsed:1,displayDataTypes:!1})})},[x,o]),ce=(0,m.useMemo)(function(){if(!x)return null;var B=x.total,L=B===void 0?0:B,ne=x.infos,ae=ne===void 0?[]:ne;return(0,e.jsxs)("div",{className:Q.memory,children:[(0,e.jsxs)("div",{className:Q.memory_total,children:["\u603B\u6570\uFF1A",L]}),(0,e.jsx)("div",{children:ae.map(function(J){return(0,e.jsxs)("div",{className:Q.memory__item,children:[(0,e.jsx)("div",{children:Qe()(J.timestamp).format("YYYY-MM-DD HH:mm:ss")}),(0,e.jsx)("div",{className:Q.memory__item_content,children:J.content}),(0,e.jsxs)("div",{children:[(0,e.jsx)("span",{className:Q.memory__item_red,children:"attention: "}),(0,e.jsx)("span",{className:Q.memory__item_blue,children:J.attention})]})]})})})]})},[x]);return(0,e.jsxs)("div",{className:Q.wrapper,children:[h&&T(),x?p?ce:W:O]})},me=ln,pe={search:"search___kvGWZ",search__btn:"search__btn___IeAqs",search__btn_insert:"search__btn_insert___uWpFj",search_area:"search_area___oVSnI",search__multiple:"search__multiple___Ascb8"},rn=Ae.Z.TextArea,un='{"content":"\u6211\u662F\u4E00\u4E2A\u597D\u4EBA", "attention":75, "divide":["11", "22"]}',Z=["qa","embedding","impress","strategy","memory","mission","gpt","doc"],dn=function(t){var n=t.chatModel,r=t.dispatch,o=n.isConnect,u=(0,m.useState)(un),h=C()(u,2),i=h[0],p=h[1],_=(0,m.useState)(!1),A=C()(_,2),y=A[0],x=A[1],k=(0,m.useState)(!1),R=C()(k,2),E=R[0],N=R[1],K=(0,m.useState)(!1),O=C()(K,2),T=O[0],W=O[1],ce=(0,m.useState)(Z[0]),B=C()(ce,2),L=B[0],ne=B[1],ae=Fe.ZP.useMessage(),J=C()(ae,2),w=J[0],ie=J[1],xe=function(l){return new Promise(function(d,g){if(!o){w.warning("\u5F53\u524Dwebsocket\u79BB\u7EBF\uFF0C\u8BF7\u5148\u5EFA\u7ACB\u8FDE\u63A5"),d(null);return}if(!l){d(null);return}var M=U(),S=M.chatUid;(0,F.gM)({uid:S,method:"get_task_context",seq:"2333",data:{task_id:l}}).then(function(f){if(f&&f.success){var I;d((I=f==null?void 0:f.task_context)!==null&&I!==void 0?I:{})}else d(null)})})},je=function(l){return new Promise(function(d,g){if(!o){w.warning("\u5F53\u524Dwebsocket\u79BB\u7EBF\uFF0C\u8BF7\u5148\u5EFA\u7ACB\u8FDE\u63A5"),d(null);return}if(!l){d(null);return}var M=U(),S=M.chatUid;(0,F.HD)({uid:S,method:"get_llm_result",seq:"2333",data:{task_id:l}}).then(function(f){if(f&&f.success){var I,V;d((I=f==null||(V=f.data)===null||V===void 0?void 0:V.result)!==null&&I!==void 0?I:{})}else d(null)})})},Se=function(l){return new Promise(function(d,g){if(!o){w.warning("\u5F53\u524Dwebsocket\u79BB\u7EBF\uFF0C\u8BF7\u5148\u5EFA\u7ACB\u8FDE\u63A5"),d(null);return}if(!l){d(null);return}var M=U(),S=M.chatUid;(0,F.HD)({uid:S,method:"get_qa_by_content",seq:"2333",data:{content:l}}).then(function(f){if(f&&f.success){var I,V;d((I=f==null||(V=f.data)===null||V===void 0?void 0:V.result)!==null&&I!==void 0?I:{})}else d(null)})})},Ee=function(l){return new Promise(function(d,g){if(!o){w.warning("\u5F53\u524Dwebsocket\u79BB\u7EBF\uFF0C\u8BF7\u5148\u5EFA\u7ACB\u8FDE\u63A5"),d(null);return}if(!l){d(null);return}var M=U(),S=M.chatUid;(0,F.HD)({uid:S,method:"get_memory_by_content",seq:"2333",data:{content:l}}).then(function(f){if(f&&f.success){var I,V;d((I=f==null||(V=f.data)===null||V===void 0?void 0:V.result)!==null&&I!==void 0?I:{})}else d(null)})})},be=function(){return new Promise(function(l,d){if(!o){l(null);return}var g=U(),M=g.chatUid;(0,F.rO)({uid:M}).then(function(S){if(S&&S.success){var f;l((f=S==null?void 0:S.data)!==null&&f!==void 0?f:{})}else l(null)})})},Ce=function(){return new Promise(function(l,d){if(!o){l(null);return}var g=U(),M=g.chatUid;(0,F.kg)({robot_id:"agent001",limit:100,uids:[M]}).then(function(S){if(S&&S.success){var f;l((f=S==null?void 0:S.data)!==null&&f!==void 0?f:{})}else l(null)})})},G=function(l){return new Promise(function(d,g){if(!o){w.warning("\u5F53\u524Dwebsocket\u79BB\u7EBF\uFF0C\u8BF7\u5148\u5EFA\u7ACB\u8FDE\u63A5"),d(null);return}if(!l){d(null);return}var M=U(),S=M.chatUid;(0,F.wb)({uid:S,limit:50,cursor:0,type:l}).then(function(f){if(f&&f.success){var I;d((I=f==null?void 0:f.data)!==null&&I!==void 0?I:{})}else d(null)})})},ue=[{key:Z[0],label:"QA\u68C0\u7D22",children:(0,e.jsx)(me,{name:"QA\u68C0\u7D22",visible:L===Z[0],action:Se,search:!0,tips:"\u8BF7\u8F93\u5165QA\u68C0\u7D22\u6761\u4EF6"})},{key:Z[1],label:"\u957F\u671F\u8BB0\u5FC6embedding",children:(0,e.jsx)(me,{name:"\u957F\u671F\u8BB0\u5FC6embedding",visible:L===Z[1],action:Ee,search:!0,tips:"\u8BF7\u8F93\u5165\u957F\u671F\u8BB0\u5FC6\u68C0\u7D22\u6761\u4EF6"})},{key:Z[2],label:"\u5370\u8C61\u67E5\u8BE2",children:(0,e.jsx)(me,{name:"\u5370\u8C61\u67E5\u8BE2",visible:L===Z[2],action:be})},{key:Z[3],label:"\u7B56\u7565\u67E5\u8BE2",children:(0,e.jsx)(me,{name:"\u7B56\u7565\u67E5\u8BE2",visible:L===Z[3],action:Ce})},{key:Z[4],label:"\u8BB0\u5FC6\u67E5\u8BE2",children:(0,e.jsx)(me,{name:"\u8BB0\u5FC6\u67E5\u8BE2",visible:L===Z[4],search:!0,isMemory:!0,action:G})},{key:Z[5],label:"\u4EFB\u52A1\u4E0A\u4E0B\u6587",children:(0,e.jsx)(me,{name:"\u4EFB\u52A1\u4E0A\u4E0B\u6587",visible:L===Z[5],action:xe,search:!0,tips:"\u8BF7\u8F93\u5165task_id"})},{key:Z[6],label:"\u4EFB\u52A1\u5927\u6A21\u578B\u56DE\u590D",children:(0,e.jsx)(me,{name:"\u4EFB\u52A1\u5927\u6A21\u578B\u56DE\u590D",visible:L===Z[6],action:je,search:!0,tips:"\u8BF7\u8F93\u5165task_id"})},{key:Z[7],label:"\u6587\u6863\u64CD\u4F5C\u4E0E\u67E5\u8BE2",children:(0,e.jsx)(cn,{visible:L===Z[7]})}],de=function(l){var d=l.target.value;p(d)},Me=function(l){ne(l)},Te=function(){if(!(!i||!i.trim())){var l={};try{l=JSON.parse(i)}catch(M){w.error("JSON\u89E3\u6790\u5931\u8D25\uFF0C\u8BF7\u68C0\u67E5\u8F93\u5165\u5185\u5BB9");return}N(!0);var d=U(),g=d.chatUid;(0,F.HD)({uid:g,method:"insert_stream",seq:"2333",data:l}).then(function(M){M&&M.success?w.success("\u601D\u7EEA\u63D2\u5165\u6210\u529F"):Ie.Z.error({title:"\u5931\u8D25",content:M.msg?M.msg:"\u601D\u7EEA\u63D2\u5165\u5931\u8D25",okText:"\u786E\u5B9A"}),N(!1)}).catch(function(M){N(!1)})}},ke=function(){if(!i||!i.trim()){w.warning("\u8BF7\u8F93\u5165\u7B56\u7565\u5185\u5BB9");return}x(!0);var l=U(),d=l.chatUid;(0,F.iZ)({uid:d,content:i,robot_id:"agent001",attention:60}).then(function(g){g&&g.success?w.success("\u7B56\u7565\u63D2\u5165\u6210\u529F"):Ie.Z.error({title:"\u5931\u8D25",content:g.msg?g.msg:"\u7B56\u7565\u63D2\u5165\u5931\u8D25",okText:"\u786E\u5B9A"}),x(!1)}).catch(function(g){x(!1)})},Ue=function(){if(!i||!i.trim()){w.warning("\u8BF7\u8F93\u5165\u89D2\u8272\u5185\u5BB9");return}W(!0);var l=U(),d=l.chatUid;(0,F.HD)({uid:d,method:"set_role_transform",seq:"2333",data:{content:i}}).then(function(g){g&&g.success?(w.success("\u5207\u6362\u89D2\u8272\u6210\u529F"),r({type:"chatModel/fetchGetRole",payload:{uid:d,method:"get_robot_role",seq:"2333"}})):Ie.Z.error({title:"\u5931\u8D25",content:g.msg?g.msg:"\u5207\u6362\u89D2\u8272\u5931\u8D25",okText:"\u786E\u5B9A"}),W(!1)}).catch(function(g){W(!1)})};return(0,e.jsxs)("div",{className:pe.search,children:[(0,e.jsx)(rn,{className:pe.search_area,placeholder:"\u8BF7\u8F93\u5165\u7B56\u7565/JSON\u683C\u5F0F\u601D\u7EEA\u6D41",value:i,onChange:de,autoSize:{minRows:4,maxRows:4}}),(0,e.jsxs)("div",{className:pe.search__btn,children:[(0,e.jsx)(se.ZP,{className:pe.search__btn_insert,type:"primary",disabled:!o||y||T,loading:E,onClick:Te,children:"\u63D2\u5165\u601D\u7EEA\u6D41"}),(0,e.jsx)(se.ZP,{className:pe.search__btn_insert,type:"primary",disabled:!o||E||T,onClick:ke,loading:y,children:"\u63D2\u5165\u7B56\u7565"}),(0,e.jsx)(se.ZP,{className:pe.search__btn_insert,type:"primary",disabled:!o||E||y,onClick:Ue,loading:T,children:"\u6539\u53D8\u89D2\u8272"})]}),(0,e.jsx)("div",{className:pe.search__multiple,children:(0,e.jsx)(rt.Z,{value:L,onChange:Me,items:ue})}),ie]})},hn=(0,oe.connect)(function(c){var t=c.chatModel;return{chatModel:t}})(dn),ye={wrapper:"wrapper___k564j",content:"content___LEixu",main:"main___PTQMg",onlyPc:"onlyPc___v51Cl"};function _n(){return(0,e.jsxs)("div",{className:ye.wrapper,children:[(0,e.jsx)("div",{className:"".concat(ye.content," ").concat(ye.main),children:(0,e.jsx)(Zt,{})}),(0,e.jsx)("div",{className:"".concat(ye.content," ").concat(ye.onlyPc),children:(0,e.jsx)(qt,{})}),(0,e.jsx)("div",{className:"".concat(ye.content," ").concat(ye.onlyPc),children:(0,e.jsx)(hn,{})})]})}}}]);