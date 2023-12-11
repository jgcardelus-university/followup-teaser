### What's in this folder?

This folder contains a component, a hook and view.

The usePagination hook handles paginated views. It fetches
the data and handles state and actions for components that use it.

It exposes methods to navigate and filter the paginated resource.

The list-panel-view is a component that is used in views that show paginated resources, for example, in the [Apartments view](https://followup.jgcardelus.com/dash/apartments).

It is tighlty related to the usePaginated hook.

The dash.members.$memberId.groups is a view that shows the groups of which the user is a member of.
