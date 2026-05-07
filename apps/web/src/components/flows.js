let m = require("mithril");
let Sortable = require("sortablejs");
let ConfirmModal = require("./confirm_modal");

class Flows {
  constructor() {
    this.items = [];
    this.onReorderCallback = null;
    this.onDeleteCallback = null;
    this.deleteTarget = null;
    this.isDeleting = false;
    this.error = null;
  }

  _reorderItems(oldIndex, newIndex) {
    if (oldIndex === newIndex) {
      return;
    }

    let items = this.items.slice();

    let moved = items.splice(oldIndex, 1)[0];
    items.splice(newIndex, 0, moved);
    this.items = items;

    if (typeof this.onReorderCallback === "function") {
      let mapping = Object.fromEntries(items.map(function (item, index) {
        return [item.id, index + 1];
      }));

      this.onReorderCallback(mapping);
    }
  }

  view(vnode) {
    this.items = vnode.attrs.flows;
    this.onReorderCallback = vnode.attrs.onReorder;
    this.onDeleteCallback = vnode.attrs.onDelete;
    let campaignId = vnode.attrs.campaignId;

    if (this.items.length === 0) {
      return m("div.text-muted", "No flows found.");
    }

    let self = this;

    return m("div", [
      this.error
        ? m(".alert.alert-danger", this.error)
        : null,
      m(
        "ul.list-group",
        {
          oncreate: function (vnode) {
            Sortable.create(vnode.dom, {
              onEnd: function (e) {
                this._reorderItems(e.oldIndex, e.newIndex);
                m.redraw();
              }.bind(this),
            });
          }.bind(this),
        },
        this.items.map(function (flow) {
          return m(
            "li.list-group-item.d-flex.align-items-center.justify-content-between",
            {
              class: flow.isEnabled ? "" : "flows-item-disabled",
            },
            [
              m("div", [
                m(
                  "a.fw-semibold.text-decoration-none",
                  {
                    href:
                      `#!/core/campaigns/${campaignId}/flows/${flow.id}`,
                  },
                  flow.name,
                ),
                m(
                  "div.small.text-muted",
                  [
                    m("i", {
                      class:
                        flow.actionType === "render"
                          ? "fa fa-file-alt"
                          : "fa fa-external-link-alt",
                      title: flow.actionType,
                    }),
                    flow.redirectUrl
                      ? m("span.ms-2.text-break", flow.redirectUrl)
                      : null,
                  ],
                ),
              ]),
              m(
                "button.btn.btn-sm",
                {
                  type: "button",
                  onclick: function () {
                    self.deleteTarget = flow;
                    self.error = null;
                  },
                },
                m("i", { class: "fa fa-trash", title: "Delete" }),
              ),
            ],
          );
        }),
      ),
      m(ConfirmModal, {
        isOpen: Boolean(this.deleteTarget),
        isBusy: this.isDeleting,
        title: "Delete flow",
        body: this.deleteTarget
          ? m(
              "p.mb-0",
              `Are you sure you want to delete \"${
                this.deleteTarget.name || this.deleteTarget.id
              }\"?`,
            )
          : null,
        confirmText: this.isDeleting ? "Deleting..." : "Delete",
        cancelText: "Cancel",
        onCancel: function () {
          if (this.isDeleting) {
            return;
          }
          this.deleteTarget = null;
        }.bind(this),
        onConfirm: function () {
          if (typeof this.onDeleteCallback !== "function") {
            this.error = "Delete handler is not configured.";
            this.deleteTarget = null;
            return;
          }

          this.isDeleting = true;
          this.error = null;
          this.onDeleteCallback(this.deleteTarget);
        }.bind(this),
      }),
    ]);
  }
}

module.exports = Flows;
