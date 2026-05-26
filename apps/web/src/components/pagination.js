var m = require("mithril");
var i18n = require("../i18n");

class Pagination {
  navigate(toPage, pagination) {
    let queryParams = Object.assign({}, pagination, { page: toPage });
    delete queryParams.total;

    let route = m.route.get().split("?")[0];
    m.route.set(route, queryParams);
  }

  view(vnode) {
    let pagination = vnode.attrs.pagination;
    if (pagination.total === 0) return null;

    let page = pagination.page;
    let totalPages = Math.ceil(pagination.total / pagination.pageSize);

    return m(
      ".d-flex.align-items-center.justify-content-between.mt-3",
      [
        page > 1
          ? m(
            "a.nav-item.nav-link",
            {
              type: "button",
              disabled: page <= 1,
              onclick: function () {
                this.navigate(page - 1, pagination);
              }.bind(this),
            },
            i18n.t("common.previous"),
          )
          : m("div"),
        m("div", i18n.t("common.pageOf", { page: page, totalPages: totalPages })),
        page < totalPages
          ? m(
              "a.nav-item.nav-link",
              {
                type: "button",
                onclick: function () {
                  this.navigate(page + 1, pagination);
                }.bind(this),
              },
              i18n.t("common.next"),
            )
          : m("div"),
      ],
    );
  }
}

module.exports = Pagination;
