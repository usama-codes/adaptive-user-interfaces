# frozen_string_literal: true

module IfcModelsHelper
  def ifc_model_data_object(all_models, shown_models)
    all_converted_models = converted_ifc_models(all_models)

    {
      models: ifc_model_models(all_converted_models),
      shown_models: ifc_shown_models(all_converted_models, shown_models),
      projects: [{ id: @project.identifier, name: @project.name }],
      xkt_attachment_ids: ifc_model_xkt_attachment_ids(all_converted_models),
      permissions: {
        manage_ifc_models: User.current.allowed_in_project?(:manage_ifc_models, @project),
        manage_bcf: User.current.allowed_in_project?(:manage_bcf, @project)
      }
    }
  end

  def converted_ifc_models(ifc_models)
    ifc_models.select(&:converted?)
  end

  def ifc_model_models(all_models)
    all_converted_models = converted_ifc_models(all_models)

    all_converted_models.map do |ifc_model|
      {
        id: ifc_model.id,
        name: ifc_model.title,
        default: ifc_model.is_default
      }
    end
  end

  def ifc_shown_models(all_models, shown_models)
    if shown_models.empty?
      return all_models.select(&:is_default).map(&:id)
    end

    converted_ifc_models(all_models)
      .select { |model| shown_models.include?(model.id) }
      .map(&:id)
  end

  def ifc_model_xkt_attachment_ids(models)
    models.to_h { |model| [model.id, model.xkt_attachment.id] }
  end
end
