require "open_project/custom_styles/design"

OpenProject::CustomStyles::ColorThemes::BIM_THEME_NAME = "OpenProject BIM".freeze

module OpenProject::Bim
  module Patches
    module ColorThemesPatch
      def self.included(base)
        class << base
          prepend ClassMethods
        end
      end

      module ClassMethods
        def themes
          if OpenProject::Configuration.bim?
            super + [bim_theme]
          else
            super
          end
        end

        def bim_theme
          {
            theme: OpenProject::CustomStyles::ColorThemes::BIM_THEME_NAME,
            colors: {
              "primary-button-color" => OpenProject::CustomStyles::ColorThemes::PRIMER_PRIMARY_BUTTON_COLOR,
              "header-bg-color" => "#05002C",
              "accent-color" => "#275BB5",
              "main-menu-bg-color" => "#0E2045",
              "main-menu-bg-selected-background" => "#3270DB",
              # TODO 'new-feature-teaser-image' => '#{image-url("bim/new_feature_teaser.jpg")}'
            },
            logo: "bim/logo_openproject_bim_big.png"
          }
        end
      end
    end
  end
end
