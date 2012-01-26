(function() {
  var $;
  var __hasProp = Object.prototype.hasOwnProperty, __extends = function(child, parent) {
    for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; }
    function ctor() { this.constructor = child; }
    ctor.prototype = parent.prototype;
    child.prototype = new ctor;
    child.__super__ = parent.prototype;
    return child;
  }, __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };
  $ = jQuery;
  window.ChangePlan = (function() {
    __extends(ChangePlan, Backbone.Model);
    function ChangePlan() {
      ChangePlan.__super__.constructor.apply(this, arguments);
    }
    ChangePlan.prototype.get_rental_plan = function() {
      var rental_plan;
      rental_plan = rental_plan_collection.find(__bind(function(rp) {
        return rp.get("pk") === this.get("plan");
      }, this));
      return rental_plan;
    };
    return ChangePlan;
  })();
  window.RentalPlan = (function() {
    __extends(RentalPlan, Backbone.RelationalModel);
    function RentalPlan() {
      RentalPlan.__super__.constructor.apply(this, arguments);
    }
    RentalPlan.prototype.urlRoot = "/api/v1/rental_plan/";
    return RentalPlan;
  })();
  window.RentalPlanCollection = (function() {
    __extends(RentalPlanCollection, Backbone.Collection);
    function RentalPlanCollection() {
      RentalPlanCollection.__super__.constructor.apply(this, arguments);
    }
    RentalPlanCollection.prototype.urlRoot = "/api/v1/rental_plan/";
    RentalPlanCollection.prototype.model = RentalPlan;
    return RentalPlanCollection;
  })();
  window.MemberRentalPlan = (function() {
    __extends(MemberRentalPlan, Backbone.RelationalModel);
    function MemberRentalPlan() {
      MemberRentalPlan.__super__.constructor.apply(this, arguments);
    }
    MemberRentalPlan.prototype.url = "/api/v1/member_rental_plan/";
    MemberRentalPlan.prototype.relations = [
      {
        type: Backbone.HasOne,
        key: 'rental_plan',
        relatedModel: 'RentalPlan'
      }
    ];
    return MemberRentalPlan;
  })();
  window.change_plan = new ChangePlan();
  window.rental_plan_collection = new RentalPlanCollection();
  window.rental_plan_collection.fetch();
  window.member_rental_plan = new MemberRentalPlan();
  window.member_rental_plan.fetch();
  $(document).ready(function() {
    window.ChangePlanView = (function() {
      __extends(ChangePlanView, Backbone.View);
      function ChangePlanView() {
        this.change_plan = __bind(this.change_plan, this);
        ChangePlanView.__super__.constructor.apply(this, arguments);
      }
      ChangePlanView.prototype.el = "#content";
      ChangePlanView.prototype.events = {
        "submit #id_form_change_plan": "change_plan"
      };
      ChangePlanView.prototype.initialize = function() {
        return new ChangePlanDialogView({
          model: this.model
        });
      };
      ChangePlanView.prototype.change_plan = function(eventObject) {
        var $form, plan;
        $form = $(eventObject.target);
        plan = parseInt($form.find("input[name=0-plan]").val(), 10);
        this.model.set({
          plan: plan
        }, {
          silent: true
        });
        this.model.change();
        return false;
      };
      return ChangePlanView;
    })();
    window.ChangePlanDialogView = (function() {
      __extends(ChangePlanDialogView, Backbone.View);
      function ChangePlanDialogView() {
        this.render = __bind(this.render, this);
        ChangePlanDialogView.__super__.constructor.apply(this, arguments);
      }
      ChangePlanDialogView.prototype.el = "#cboxContent";
      ChangePlanDialogView.prototype.initialize = function() {
        this.template = _.template($("#change-plan-template").html());
        return this.model.bind("change", this.render);
      };
      ChangePlanDialogView.prototype.render = function() {
        var context, current_rental_plan, new_rental_plan;
        current_rental_plan = window.member_rental_plan.get("rental_plan");
        new_rental_plan = this.model.get_rental_plan();
        context = {
          current_rental_plan: current_rental_plan.toJSON(),
          new_rental_plan: new_rental_plan.toJSON(),
          charge_for_the_rest_of_month: 0,
          will_be_billed: 0,
          plan_starts: "03/27/10",
          payment_card: "MasterCard XXXX XXXX XXXX 9376"
        };
        console.log(context);
        return $.colorbox({
          html: this.template(context),
          overlayClose: false,
          onComplete: function() {
            return $(".dialog-close-button").click(function() {
              $.colorbox.close();
              return false;
            });
          }
        });
      };
      return ChangePlanDialogView;
    })();
    window.Gamemine = (function() {
      __extends(Gamemine, Backbone.Router);
      function Gamemine() {
        Gamemine.__super__.constructor.apply(this, arguments);
      }
      Gamemine.prototype.initialize = function() {
        if (window.location.pathname === "/Rent/Plan/") {
          return this.change_plan_view = new ChangePlanView({
            model: window.change_plan
          });
        }
      };
      return Gamemine;
    })();
    return window.App = new Gamemine();
  });
}).call(this);
