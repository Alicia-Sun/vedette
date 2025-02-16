import { ref as h, onMounted as b, onBeforeUnmount as y, inject as E } from "vue";
const L = {
  setup(p, { emit: l, expose: o }) {
    const c = h(null);
    function u(s) {
      c.value && c.value.contentWindow.postMessage(s, "*");
    }
    function n(s) {
      var m, g;
      (m = s == null ? void 0 : s.data) != null && m.emit && l(s.data.emit, (g = s.data) == null ? void 0 : g.value);
    }
    return b(() => {
      c.value.contentWindow.addEventListener("message", n);
    }), y(() => {
      c.value.contentWindow.removeEventListener("message", n);
    }), o({ triggerEmit: n, postMessage: u }), { triggerEmit: n, postMessage: u, elem: c };
  },
  template: '<iframe ref="elem" v-bind="$attrs"></iframe>'
}, M = {
  props: ["targetOrigin", "enableRpc"],
  props: {
    targetOrigin: {
      type: String
    },
    enableRpc: {
      type: Boolean,
      default: !1
    }
  },
  setup(p, { emit: l }) {
    const o = E("trame"), c = p.targetOrigin, u = p.enableRpc;
    function n(a) {
      c ? window.parent.postMessage(a, c) : window.postMessage(a, "*");
    }
    o.state.ready && n({
      event: "stateReady"
    });
    function s(a) {
      var e, t, r;
      (e = a == null ? void 0 : a.data) != null && e.emit && l(a.data.emit, (t = a.data) == null ? void 0 : t.value), (r = a == null ? void 0 : a.data) != null && r.state && o.state.update(a.data.state);
    }
    function m(a, e, t) {
      const r = (...d) => {
        n({
          rpcCallback: {
            channel: "trame.state.watch",
            id: a,
            payload: {
              stateVars: d
            }
          }
        });
      };
      o.state.watch(e, r);
    }
    function g(a, e) {
      const t = (r, ...d) => {
        n({
          rpcCallback: {
            channel: "trame.trigger",
            id: a,
            payload: {
              error: r,
              result: d
            }
          }
        });
      };
      o.trigger(e.name, e.args, e.kwargs).then(t.bind(null, !1)).catch(t.bind(null, !0));
    }
    function k(a, e) {
      const t = o.state.get(e.key);
      n({
        rpcCallback: {
          channel: "trame.state.get",
          id: a,
          payload: {
            result: t
          }
        }
      });
    }
    function f(a) {
      var d;
      if (a.origin !== c || !((d = a == null ? void 0 : a.data) != null && d.rpc))
        return;
      const { obj: e, method: t, args: r } = a.data.rpc;
      switch (e) {
        case "trame":
          switch (t) {
            case "trigger":
              {
                const { eventId: i } = a.data.meta;
                g(i, r);
              }
              break;
          }
          break;
        case "trame.state":
          switch (t) {
            case "watch":
              {
                const { eventId: i } = a.data.meta;
                m(i, r);
              }
              break;
            case "get":
              {
                const { eventId: i } = a.data.meta;
                k(i, r);
              }
              break;
            default:
              if (typeof o.state[t] != "function") {
                console.error(`unsupported trame.state rpc; ${t}`);
                return;
              }
              o.state[t](...r);
              break;
          }
          break;
        default:
          console.error(`unsupported rpc: ${e}`);
      }
    }
    return b(() => {
      u && window.addEventListener("message", f), window.addEventListener("message", s);
    }), y(() => {
      u && window.removeEventListener("message", f), window.removeEventListener("message", s);
    }), { postMessage: n, triggerEmit: s };
  }
}, w = {
  IFrame: L,
  Communicator: M
};
function O(p) {
  Object.keys(w).forEach((l) => {
    p.component(l, w[l]);
  });
}
export {
  O as install
};
