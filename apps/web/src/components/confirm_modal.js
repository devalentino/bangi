var m = require("mithril");
var i18n = require("../i18n");

class ConfirmModal {
  view(vnode) {
    if (!vnode.attrs.isOpen) {
      return null;
    }

    return m("div", [
      m(
        ".modal.fade.show",
        {
          style: "display: block;",
          tabindex: "-1",
          role: "dialog",
        },
        m(".modal-dialog", { role: "document" }, [
          m(".modal-content", [
            m(".modal-header", [
              m("h5.modal-title", vnode.attrs.title || i18n.t("common.confirm")),
              m(
                "button.btn-close",
                {
                  type: "button",
                  onclick: vnode.attrs.onCancel,
                  disabled: vnode.attrs.isBusy,
                },
                "",
              ),
            ]),
            m(".modal-body", vnode.attrs.body || null),
            m(".modal-footer", [
              m(
                "button.btn.btn-secondary",
                {
                  type: "button",
                  onclick: vnode.attrs.onCancel,
                  disabled: vnode.attrs.isBusy,
                },
                vnode.attrs.cancelText || i18n.t("common.cancel"),
              ),
              m(
                "button.btn.btn-danger",
                {
                  type: "button",
                  onclick: vnode.attrs.onConfirm,
                  disabled: vnode.attrs.isBusy,
                },
                vnode.attrs.confirmText || i18n.t("common.confirm"),
              ),
            ]),
          ]),
        ]),
      ),
      m(".modal-backdrop.fade.show"),
    ]);
  }
}

module.exports = ConfirmModal;
