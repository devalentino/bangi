let m = require("mithril");
let CoreCampaignModel = require("../models/core_campaign");
let CoreFlowsModel = require("../models/core_flows");
let Flows = require("../components/flows");

class CoreCampaignView {
  constructor(vnode) {
    this.campaignModel = new CoreCampaignModel(m.route.param("campaignId"));
    this.flowsModel = new CoreFlowsModel(m.route.param("campaignId"));
  }

  oninit() {
    let campaignId = m.route.param("campaignId");
    if (campaignId !== "new") {
      this.campaignModel.fetch();
      this.flowsModel.fetch({
        page: 1,
        pageSize: 1000,
        sortBy: "orderValue",
        sortOrder: "asc",
      });
    }
  }

  view() {
    let isNew = this.campaignModel.campaignId === "new";

    return m(
      ".container-fluid.pt-4.px-4",
      m(".row.g-4", [
        m(".col-12.col-xl-6", [
          m(".bg-light.rounded.h-100.p-4", [
            m(
              "h6.mb-4",
              isNew ? "New Core Campaign" : "Core Campaign Modification",
            ),
            this.campaignModel.isLoading
              ? m("div", "Loading campaign...")
              : [
                  this.campaignModel.error
                    ? m(".alert.alert-danger", this.campaignModel.error)
                    : null,
                  this.campaignModel.successMessage
                    ? m(
                        ".alert.alert-success",
                        this.campaignModel.successMessage,
                      )
                    : null,
                  m(
                    "form",
                    {
                      onsubmit: function (event) {
                        event.preventDefault();
                        this.campaignModel.save();
                      }.bind(this),
                      onreset: function (event) {
                        event.preventDefault();
                        this.campaignModel.resetForm();
                      }.bind(this),
                    },
                    [
                      m(".mb-3", [
                        m("label.form-label", { for: "campaignName" }, "Name"),
                        m("input.form-control", {
                          type: "text",
                          id: "campaignName",
                          placeholder: "Campaign Name",
                          value: this.campaignModel.form.name,
                          oninput: function (event) {
                            this.campaignModel.form.name = event.target.value;
                          }.bind(this),
                        }),
                      ]),
                      m(".mb-3", [
                        m(
                          "label.form-label",
                          { for: "internalProcessUrl" },
                          "Internal Process URL",
                        ),
                        m(
                          "#internalProcessUrl.form-control-plaintext",
                          this.campaignModel.form.internalProcessUrl,
                        ),
                      ]),
                      m(".row.g-3", [
                        m(".col-sm-12.col-md-6", [
                          m(
                            "label.form-label",
                            { for: "costModel" },
                            "Cost Model",
                          ),
                          m(
                            "select.form-select",
                            {
                              id: "costModel",
                              value: this.campaignModel.form.costModel,
                              onchange: function (event) {
                                this.campaignModel.form.costModel =
                                  event.target.value;
                              }.bind(this),
                            },
                            [
                              m("option", { value: "cpc" }, "CPC"),
                              m("option", { value: "cpm" }, "CPM"),
                              m("option", { value: "cpl" }, "CPL"),
                              m("option", { value: "cpa" }, "CPA"),
                              m("option", { value: "cpi" }, "CPI"),
                            ],
                          ),
                        ]),
                      ]),
                      m(".row.g-3.mt-1", [
                        m(".col-sm-12.col-md-6", [
                          m(
                            "label.form-label",
                            { for: "costValue" },
                            "Cost Value",
                          ),
                          m("input.form-control", {
                            type: "number",
                            id: "costValue",
                            placeholder: "Cost Value",
                            value: this.campaignModel.form.costValue,
                            oninput: function (event) {
                              this.campaignModel.form.costValue =
                                event.target.value;
                            }.bind(this),
                          }),
                        ]),
                        m(".col-sm-12.col-md-6", [
                          m(
                            "label.form-label",
                            { for: "currency" },
                            "Currency",
                          ),
                          m(
                            "select.form-select",
                            {
                              id: "currency",
                              value: this.campaignModel.form.currency,
                              onchange: function (event) {
                                this.campaignModel.form.currency =
                                  event.target.value;
                              }.bind(this),
                            },
                            [
                              m("option", { value: "usd" }, "USD"),
                              m("option", { value: "eur" }, "EUR"),
                              m("option", { value: "uah" }, "UAH"),
                            ],
                          ),
                        ]),
                      ]),
                      m(".mb-3.mt-3", [
                        m(
                          "label.form-label",
                          { for: "statusMapper" },
                          "Status Mapper",
                        ),
                        m("textarea.form-control", {
                          id: "statusMapper",
                          rows: "4",
                          placeholder:
                            '{"parameter":"state","mapping":{"approved":"APPROVED","rejected":"REJECTED"}}',
                          class: "font-monospace",
                          value: this.campaignModel.form.statusMapperText,
                          oninput: function (event) {
                            this.campaignModel.form.statusMapperText =
                              event.target.value;
                          }.bind(this),
                        }),
                        m(
                          ".form-text",
                          "JSON with parameter string and mapping object (string to string).",
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
        m(".col-12.col-xl-6", [
          m(".bg-light.rounded.h-100.p-4", [
            m(
              ".d-flex.align-items-center.justify-content-between.mb-4",
              [
                m("h6.mb-0", "Flows"),
                this.campaignModel.campaignId
                  && this.campaignModel.campaignId !== "new"
                  ? m(
                      "a.btn.btn-primary.btn-sm",
                      {
                        href: `#!/core/campaigns/${this.campaignModel.campaignId}/flows/new`,
                      },
                      "New Flow",
                    )
                  : null,
              ],
            ),
            this.flowsModel.isLoading
              ? m("div", "Loading flows...")
              : [
                  this.flowsModel.error
                    ? m(".alert.alert-danger", this.flowsModel.error)
                    : null,
                  m(Flows, {
                    campaignId: this.campaignModel.campaignId,
                    flows: this.flowsModel.items,
                    onReorder: function (mapping) {
                      this.flowsModel.updateOrderBulk(
                        this.campaignModel.campaignId,
                        mapping,
                      );
                    }.bind(this),
                    onDelete: function (flow) {
                      return this.flowsModel.deleteFlow(flow.id).then(function () {
                        this.flowsModel.fetch({
                          page: 1,
                          pageSize: 1000,
                          sortBy: "orderValue",
                          sortOrder: "asc",
                        });
                      }.bind(this));
                    }.bind(this),
                  }),
                ],
          ]),
        ]),
      ]),
    );
  }
}

module.exports = CoreCampaignView;
