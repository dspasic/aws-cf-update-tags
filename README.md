# Updating Tags for Existing CloudFormation Stacks

This script is iterating through all root stacks and updates the tags.

It uses the UsePreviousTemplate and UsePreviousValue for each parameter to
achieve this task without a need to touch the templates.

In case all declarations are already done, update_stack function will throw an
ValidationError with a message that nothing has been changed. This is absolutely
okay (except that the design is not) and the script will just ignore this case.

To resolve the function and the environment it uses the stack name where by
convention all information can be extracted. There is one exception namely
the base stack names. In this case the environment will be set to n/a and
the function to `base`.

You can as well map function names to a more common name. This can be useful
if you want to group stacks by there product. To achieve this you have just
to adjust the FUNC_MAPS list with corresponding callbacks.

This script here will filter *only* inventory stacks and accordingly set the
tags for the matching team. So be aware of this settings, before execution.

## Naming Convention of CloudFormation Stacks

The convention of the stack name set forth that it contains three information:

* Domain/Team
* Function
* Environment

The separator for the information part is a double dash `--`. For instance, lets
assume we have a stack from the domain `bi` with the function `unique user session
visits` for the `production` environment. Then CloudFormation stack name could
look like: `bi--unq-user-sess-visits--prod`.
