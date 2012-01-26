#
# We currently do not use this file
#
$ = jQuery

class window.ChangePlan extends Backbone.Model
  get_rental_plan: ->
    rental_plan = rental_plan_collection.find((rp) =>
      return rp.get("pk") == @get("plan")
    )
    return rental_plan


class window.RentalPlan extends Backbone.RelationalModel
  urlRoot: "/api/v1/rental_plan/"


class window.RentalPlanCollection extends Backbone.Collection
  urlRoot: "/api/v1/rental_plan/"
  model: RentalPlan

class window.MemberRentalPlan extends Backbone.RelationalModel
  url: "/api/v1/member_rental_plan/"

  relations: [{
    type: Backbone.HasOne,
    key: 'rental_plan',
    relatedModel: 'RentalPlan',
  }]

window.change_plan = new ChangePlan()
window.rental_plan_collection = new RentalPlanCollection()
window.rental_plan_collection.fetch()
window.member_rental_plan = new MemberRentalPlan()
window.member_rental_plan.fetch()


$(document).ready ->

  class window.ChangePlanView extends Backbone.View
    el: "#content"
    events: {
      "submit #id_form_change_plan": "change_plan"
    }

    initialize: ->
      new ChangePlanDialogView({model: @model})

    change_plan: (eventObject) =>
      $form = $(eventObject.target)
      plan = parseInt($form.find("input[name=0-plan]").val(), 10)
      @model.set({plan: plan}, {silent: true})
      @model.change()
      return false


  class window.ChangePlanDialogView extends Backbone.View
    el: "#cboxContent"

    initialize: ->
      @template = _.template($("#change-plan-template").html())
      @model.bind("change", @render)

    render: =>
      current_rental_plan = window.member_rental_plan.get("rental_plan")
      new_rental_plan = @model.get_rental_plan()
      context = {
        current_rental_plan: current_rental_plan.toJSON(),
        new_rental_plan: new_rental_plan.toJSON(),
        charge_for_the_rest_of_month: 0,
        will_be_billed: 0,
        plan_starts: "03/27/10",
        payment_card: "MasterCard XXXX XXXX XXXX 9376",

      }
      console.log context
      $.colorbox({
        html: @template(context),
        overlayClose: false,
        onComplete: ->
          $(".dialog-close-button").click ->
            $.colorbox.close()
            return false
      })


  class window.Gamemine extends Backbone.Router
    # routes: {
    #   "change_plan": "change_plan",
    # }

    initialize: ->
      if window.location.pathname == "/Rent/Plan/"
        @change_plan_view = new ChangePlanView({model: window.change_plan})

    # change_plan: ->
    #   @


  window.App = new Gamemine()
  # Backbone.history.start()

