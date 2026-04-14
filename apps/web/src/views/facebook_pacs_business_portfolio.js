let m = require("mithril");
let FacebookPacsBusinessPortfolioModel = require("../models/facebook_pacs_business_portfolio");
let AutocompleteModule = require("@trevoreyre/autocomplete-js");
let ConfirmModal = require("../components/confirm_modal");

let Autocomplete = AutocompleteModule.default || AutocompleteModule;

class ExecutorsSearchWidget {
  constructor() {
    this.autocomplete = null;
    this.searchError = null;
    this.autocompleteRoot = null;
    this.deleteTarget = null;
    this.isDeleting = false;
    this.deleteError = null;
  }

  onremove() {
    if (this.autocomplete && this.autocomplete.destroy) {
      this.autocomplete.destroy();
    }
  }

  initAutocomplete(root, onSelect, onSearch) {
    if (this.autocomplete) {
      return;
    }

    this.autocompleteRoot = root;
    this.autocomplete = new Autocomplete(root, {
      search: function (input) {
        if (typeof onSearch !== "function") {
          this.searchError = "Search handler is not configured.";
          return Promise.resolve([]);
        }

        this.searchError = null;

        return Promise.resolve(onSearch(input)).catch(function () {
          this.searchError = "Failed to search executors.";
          return [];
        }.bind(this));
      }.bind(this),
      getResultValue: function (result) {
        return result.name;
      },
      renderResult: function (result, props) {
        return `<li ${props}>
          <div class="d-flex justify-content-between">
            <span>${result.name}</span>
          </div>
        </li>`;
      },
      onSubmit: function (result) {
        if (onSelect) {
          onSelect(result);
        }

        this.setValue("");
      },
      autoSelect: true,
      submitOnEnter: true,
    });
  }

  view(vnode) {
    let relatedExecutors = vnode.attrs.relatedExecutors || [];
    let onSelect = vnode.attrs.onSelect;
    let linkError = vnode.attrs.linkError;
    let isLinking = vnode.attrs.isLinking;
    let onRemove = vnode.attrs.onRemove;
    let onSearch = vnode.attrs.onSearch;

    return m(
      ".bg-light.rounded.h-100.p-4",
      {
        oncreate: function (node) {
          this.initAutocomplete(node.dom, onSelect, onSearch);
        }.bind(this),
      },
      [
        m("h6.mb-4", "Executors"),
        m("div", [
          m(
            "div.autocomplete.mb-3",
            m("input.form-control.border-0", {
              type: "search",
              placeholder: "Search",
            }),
            m("div", {"style": "position: relative;"}, m("ul.autocomplete-result-list")),
          ),
          this.searchError
            ? m("div.text-danger.small.mt-2", this.searchError)
            : null,
          linkError ? m("div.text-danger.small.mt-2", linkError) : null,
          isLinking ? m("div.text-muted.small.mt-2", "Linking...") : null,
          this.deleteError
            ? m("div.text-danger.small.mt-2", this.deleteError)
            : null,
        ]),
        m("div.mb-3", [
          relatedExecutors.length === 0
            ? m("div.text-muted", "No executors linked.")
            : m(
              "ul.mb-0",
              relatedExecutors.map(function (executor) {
                return m("li.d-flex.align-items-center.justify-content-between", [
                  m(
                    "a",
                    { href: `#!/facebook/pacs/executors/${executor.id}` },
                    executor.name,
                  ),
                  m(
                    "button.btn.btn-sm",
                    {
                      type: "button",
                      onclick: function () {
                        this.deleteTarget = executor;
                        this.deleteError = null;
                      }.bind(this),
                      disabled: this.isDeleting,
                      title: "Delete",
                    },
                    m("i", { class: "fa fa-trash" }),
                  ),
                ]);
              }.bind(this)),
            ),
        ]),
        m(ConfirmModal, {
          isOpen: Boolean(this.deleteTarget),
          isBusy: this.isDeleting,
          title: "Delete executor",
          body: this.deleteTarget
            ? m(
                "p.mb-0",
                `Are you sure you want to delete "${this.deleteTarget.name}"?`,
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
            if (typeof onRemove !== "function") {
              this.deleteError = "Delete handler is not configured.";
              this.deleteTarget = null;
              return;
            }

            this.isDeleting = true;
            this.deleteError = null;

            Promise.resolve(onRemove(this.deleteTarget))
              .then(function () {
                this.deleteTarget = null;
              }.bind(this))
              .catch(function () {
                this.deleteError = "Failed to delete executor.";
              }.bind(this))
              .finally(function () {
                this.isDeleting = false;
              }.bind(this));
          }.bind(this),
        }),
      ],
    );
  }
}

class FacebookPacsBusinessPortfolioView {
  constructor() {
    this.model = new FacebookPacsBusinessPortfolioModel(
      m.route.param("businessPortfolioId"),
    );
    this.isLinkingExecutor = false;
    this.executorLinkError = null;
  }

  oninit() {
    let businessPortfolioId = m.route.param("businessPortfolioId");
    if (businessPortfolioId !== "new") {
      this.model.fetch();
    }
  }

  view() {
    let isNew = this.model.businessPortfolioId === "new";
    let linkedExecutorIds = (this.model.executors || []).map(function (executor) {
      return executor.id;
    });

    return m(
      ".container-fluid.pt-4.px-4",
      m(".row.g-4", [
        m(".col-12.col-xl-4", [
          m(".bg-light.rounded.h-100.p-4", [
            m(
              "h6.mb-4",
              isNew ? "New Business Portfolio" : "Business Portfolio Modification",
            ),
            this.model.isLoading
              ? m("div", "Loading business portfolio...")
              : [
                  this.model.error
                    ? m(".alert.alert-danger", this.model.error)
                    : null,
                  this.model.successMessage
                    ? m(".alert.alert-success", this.model.successMessage)
                    : null,
                  m(
                    "form",
                    {
                      onsubmit: function (event) {
                        event.preventDefault();
                        this.model.save();
                      }.bind(this),
                      onreset: function (event) {
                        event.preventDefault();
                        this.model.resetForm();
                      }.bind(this),
                    },
                    [
                      m(".mb-3", [
                        m("label.form-label", { for: "portfolioName" }, "Name"),
                        m("input.form-control", {
                          type: "text",
                          id: "portfolioName",
                          placeholder: "Business portfolio name",
                          value: this.model.form.name,
                          oninput: function (event) {
                            this.model.form.name = event.target.value;
                          }.bind(this),
                        }),
                      ]),
                      m(".form-check.mb-3", [
                        m("input.form-check-input", {
                          type: "checkbox",
                          id: "portfolioIsBanned",
                          checked: this.model.form.isBanned,
                          onchange: function (event) {
                            this.model.form.isBanned = event.target.checked;
                          }.bind(this),
                        }),
                        m(
                          "label.form-check-label",
                          { for: "portfolioIsBanned" },
                          "Banned",
                        ),
                      ]),
                      m(
                        "button.btn.btn-primary",
                        { type: "submit" },
                        "Save changes",
                      ),
                      m(
                        "button.btn.btn-secondary.ms-2",
                        { type: "reset" },
                        "Reset",
                      ),
                    ],
                  ),
                ],
          ]),
        ]),
        isNew
          ? null
          : [
              m(".col-12.col-xl-4", [
                m(ExecutorsSearchWidget, {
                  relatedExecutors: this.model.executors,
                  isLinking: this.isLinkingExecutor,
                  linkError: this.executorLinkError,
                  onSearch: this.model.searchExecutors.bind(this.model),
                  onSelect: function (executor) {
                    if (!executor) {
                      return;
                    }

                    if (linkedExecutorIds.indexOf(executor.id) !== -1) {
                      this.executorLinkError = "Executor is already linked.";
                      return;
                    }

                    this.executorLinkError = null;
                    this.isLinkingExecutor = true;

                    this.model
                      .addExecutor(executor.id)
                      .then(function () {
                        return this.model.fetch();
                      }.bind(this))
                      .catch(function () {
                        this.executorLinkError = "Failed to link executor.";
                      }.bind(this))
                      .finally(function () {
                        this.isLinkingExecutor = false;
                      }.bind(this));
                  }.bind(this),
                  onRemove: function (executor) {
                    return this.model
                      .removeExecutor(executor.id)
                      .then(function () {
                        return this.model.fetch();
                      }.bind(this));
                  }.bind(this),
                }),
              ]),
              m(".col-12.col-xl-4", [
                m(".bg-light.rounded.h-100.p-4", [
                  m("h6.mb-4", "Ad Cabinets"),
                  this.model.adCabinets.length === 0
                    ? m("div.text-muted", "No ad cabinets linked.")
                    : m(
                        "ul.mb-0",
                        this.model.adCabinets.map(function (adCabinet) {
                          return m(
                            "li",
                            m(
                              "a",
                              { href: `#!/facebook/pacs/ad-cabinets/${adCabinet.id}` },
                              adCabinet.name,
                            ),
                          );
                        }),
                      ),
                ]),
              ]),
            ],
      ]),
    );
  }
}

module.exports = FacebookPacsBusinessPortfolioView;
